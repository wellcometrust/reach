import os

import tornado.ioloop
import tornado.web

PORT = 8888

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("page.html")

class PageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("inner_page.html")

class RobotHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("robots.txt")

def make_app():
    basedir = "/".join(os.path.abspath(__file__).split("/")[:-1])
    return tornado.web.Application([
        (r"/", MainHandler,),
        (r"/robots.txt", RobotHandler,),
        (r"/page", PageHandler,),
        (r"/page2", PageHandler,),
        (r"/page3", PageHandler,),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': basedir}),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(PORT)
    print("### Test Scrape Target")
    print("    localhost:8888")
    tornado.ioloop.IOLoop.current().start()


