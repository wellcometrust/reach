const gulp = require("gulp");
const sourcemaps = require("gulp-sourcemaps");
const uglify = require("gulp-uglify");
const concat = require('gulp-concat');

const source = require("vinyl-source-stream");
const buffer = require("vinyl-buffer");
const browserify = require("browserify");
const babel = require("babelify");

const postcss = require('gulp-postcss');
const url = require('postcss-url');

const plugins = [
      require('precss'),
      require('autoprefixer'),
      require('postcss-import'),
      url({url: "inline"}), // Inline font URLs in our CSS
      require('cssnano')
];

const paths = {
  css: {
    source: [
      "./src/**/*.css",
    ],
  },
  js: {
    source: [
      "./src/js/app.js"
    ],
  },
  images: {
    source: [
      "web/src/images/*"
    ]
  },
  favicons: {
    source: [
      "web/src/favicon/*"
    ]
  },
  build: {
    destBuildFolder: "/opt/reach/build/web/static",
    destMinCSSFileName: "styles.css",
    destMinJSFileName: "js/main.js",
    destImages: "/opt/reach/build/web/static/images",
    destFavicons: "/opt/reach/build/web/static/favicon"
  }
}

gulp.task("css", (done) => {
  gulp.src(paths.css.source)
    .pipe(buffer())
    .pipe(postcss(plugins))
    .pipe(gulp.dest(paths.build.destBuildFolder));

  done();
});

gulp.task("js", (done) => {
  const bundler = browserify({ entries: paths.js.source }, { debug: false }).transform(babel);
  bundler.bundle()
    .on("error", function (err) { console.error(err); this.emit("end"); })
    .pipe(source(paths.build.destMinJSFileName))
    .pipe(buffer())
    .pipe(uglify())
    .pipe(gulp.dest(paths.build.destBuildFolder));

  done();
});

gulp.task("images", (done) => {
    gulp.src(paths.images.source)
      .pipe(gulp.dest(paths.build.destImages));

    done();
});

gulp.task("favicons", (done) => {
    gulp.src(paths.favicons.source)
      .pipe(gulp.dest(paths.build.destFavicons));

    done();
});

gulp.task("default", gulp.series("css", "js", "images", "favicons"), (done) => done());
