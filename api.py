import json
import tempfile
import uuid
from datetime import datetime
from tools import DatabaseConnector
from flask import Flask, request, jsonify, send_file
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from wsf_scraping.spiders import who_iris_spider, nice_spider
from twisted.internet import reactor, endpoints
from scrapy.utils.log import configure_logging
from twisted.web import server, wsgi


class ScrAPI(Flask):

    def __init__(self, import_name=__package__, **kwargs):
            super(ScrAPI, self).__init__(import_name, **kwargs)
            configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
            self._init_url_rules()
            self.process = CrawlerRunner(get_project_settings())
            self.tp = reactor.getThreadPool()
            self.database = DatabaseConnector()
            self.response_meta = {"meta": {
                "project": "WSF Web Scraper"
            }}

    def __del__(self):
        self.database._close_all_spiders()
        self.database.cursor.close()
        self.database.connection.close()

    def run(self, host=None, port=None, debug=None, **options):
        super(ScrAPI, self).run(host, port, debug, **options)

    def _get_meta_response(self, res):
        res.update(self.response_meta)
        return res

    def _init_url_rules(self):
        """Attach the endpoints to run spiders and list the spiders
        that are available in the API
        """

        self.add_url_rule(
            '/spiders',
            view_func=self.list_spiders,
            methods=['GET'],
        )
        self.add_url_rule(
            '/spiders',
            view_func=self.run_spider,
            methods=['POST'],
        )
        self.add_url_rule(
            '/spiders/<int:spider_id>',
            view_func=self.close_spider,
            methods=['DELETE'],
        )
        self.add_url_rule(
            '/database',
            view_func=self.import_db,
            methods=['POST'],
        )
        self.add_url_rule(
            '/database',
            view_func=self.export_db,
            methods=['GET'],
        )
        self.add_url_rule(
            '/database',
            view_func=self.clear_scraps,
            methods=['DELETE'],
        )
        self.add_url_rule(
            '/crawls',
            view_func=self.list_crawls,
            methods=['GET'],
        )
        self.add_url_rule(
            '/crawls',
            view_func=self.stop,
            methods=['DELETE'],
        )
        self.add_url_rule(
            '/',
            view_func=self.home,
            methods=['GET'],
        )

    def home(self):
        routes = [
            {
                "url": "/spiders",
                "method": "GET"
            },
            {
                "url": "/spiders",
                "method": "POST",
                "arguments": {
                    "spider": "name of the spider to run"
                }
            },
            {
                "url": "/spiders/:spider_id",
                "method": "DELETE",
                "arguments": {
                    "spider_id": "uuid of the spider to close"
                }
            },
            {
                "url": "/crawls",
                "method": "GET"
            },
            {
                "url": "/crawls",
                "method": "DELETE"
            },
            {
                "url": "/database",
                "method": "GET"
            },
            {
                "url": "/database",
                "method": "POST",
                "arguments": {
                    "file": "json file containing the database dump"
                }
            },
            {
                "url": "/database",
                "method": "DELETE"
            }
        ]
        result = self._get_meta_response({"routes": routes})
        return jsonify(result), 200

    def list_spiders(self):
        spiders = self.process.spider_loader.list()
        return jsonify({"spiders": spiders, "status": "success"}), 200

    def run_spider(self):
        post_data = request.get_json()
        spider = post_data.get('spider')
        if spider == 'who_iris':
            spider = who_iris_spider.WhoIrisSpider()
        elif spider == 'nice':
            spider = nice_spider.NiceSpider()
        else:
            return '', 404
        spider_id = str(uuid.uuid4())
        self.process.crawl(spider, uuid=spider_id)
        crawl = self.process.join()
        self.database.insert_spider(spider.name, spider_id)
        crawl.addBoth(self.on_success)
        return jsonify({
            "data": {
              "status": "running",
              "spider": spider.name,
              "_id": spider_id
            }
        }), 200

    def on_success(self, data):
        self.database._close_all_spiders()

    def close_spider(self, spider_id):
        for crawl in self.process.crawlers:
            if crawl.spider.uuid == uuid:
                crawl.stop()
                return jsonify({
                    "data":
                        {"status": "success", "_id": spider_id}
                    }), 200
        return '', 400

    def list_crawls(self):
        crawls = self.process.crawlers
        running_spiders = []
        for crawl in crawls:
            start_time = crawl.stats.get_value('start_time')
            spider = {
                '_id':
                    crawl.spider.uuid,
                'spider':
                    crawl.spider.name,
                'start_time':
                    start_time,
                'total_time':
                    str(datetime.now() - start_time),
                'item_dropped':
                    crawl.stats.get_value('item_dropped_count'),
                'item_scraped':
                    crawl.stats.get_value('item_scraped_count'),
                'total_requests':
                    crawl.stats.get_value('downloader/request_count'),
            }

            running_spiders.append(spider)
        finished_spiders = []
        for spider in self.database.get_finished_crawls():
            finished_spiders.append(spider)
        spiders = {"crawling": running_spiders, "finished": finished_spiders}
        return jsonify({"data": {"spiders": spiders}}), 200

    def stop(self):
        self.process.stop()
        return jsonify({"data": {"status": "success"}}), 200

    def export_db(self):
        articles_rows = self.database.get_articles()
        articles = []
        now = datetime.now()
        for title, file_hash, url in articles_rows:
            articles.append({
                'title': title,
                'file_hash': file_hash,
                'url': url,
            })
        json_file = tempfile.NamedTemporaryFile()
        json_file.write(json.dumps(articles).encode('utf-8'))
        json_file.seek(0)
        return send_file(
            json_file,
            mimetype='application/json',
            as_attachment=True,
            attachment_filename=f'export-{now}.json'
        )

    def import_db(self):
        if request.files:
            data_file = request.files.get('file')
            if data_file.filename == '':
                return 'Filename must not be blank', 400
            if data_file.content_type == 'application/json':
                json_file = data_file.stream.read()
            else:
                return 'File format is not json.', 415

            try:
                json_dict = json.loads(json_file)
                for article in json_dict:
                        self.database.insert_article(
                            article.get('title'),
                            article.get('file_hash'),
                            article.get('url')
                        )

                return '', 201
            except Exception as e:
                result = {"errors": [str(e)]}
                return jsonify(result), 400
        else:
            return 'No JSON file in request', 400

    def clear_scraps(self):
        try:
            self.database.reset_scraped()
            return '', 204
        except Exception as e:
            return str(e), 500


app = ScrAPI(__name__)


def run_scrAPI():
    resource = wsgi.WSGIResource(reactor, reactor.getThreadPool(), app)
    site = server.Site(resource)
    http_server = endpoints.TCP4ServerEndpoint(reactor, 5005)
    http_server.listen(site)
    reactor.run()
    return reactor


if __name__ == '__main__':
        run_scrAPI()
