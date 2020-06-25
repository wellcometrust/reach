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
    watchFiles: "web/src/**/*.css",
    source: [
      "./web/src/**/*.css",
    ],
    destMapFolder: "."
  },
  js: {
    watchFiles: "web/src/**/*.js",
    source: [
      "./web/src/js/app.js"
    ],
    destMapFolder: "./"
  },
  build: {
    destBuildFolder: "build/web/static",
    destMinCSSFileName: "styles.css",
    destMinJSFileName: "js/main.js"
  }
}

gulp.task("css", (done) => {
  gulp.src(paths.css.source)
    .pipe(buffer())
    .pipe(sourcemaps.init())
    .pipe(postcss(plugins))
    .pipe(sourcemaps.write(paths.css.destMapFolder))
    .pipe(gulp.dest(paths.build.destBuildFolder));

  done();
});

gulp.task("js", (done) => {
  const bundler = browserify({ entries: paths.js.source }, { debug: true }).transform(babel);
  bundler.bundle()
    .on("error", function (err) { console.error(err); this.emit("end"); })
    .pipe(source(paths.build.destMinJSFileName))
    .pipe(buffer())
    .pipe(sourcemaps.init({ loadMaps: true }))
    .pipe(uglify())
    .pipe(sourcemaps.write(paths.js.destMapFolder))
    .pipe(gulp.dest(paths.build.destBuildFolder));

  done();
});

gulp.task("images", (done) => {
    gulp.src('web/src/images/*')
      .pipe(gulp.dest('build/web/static/images'));

    done();
});

gulp.task("favicons", (done) => {
    gulp.src('web/src/favicon/*')
      .pipe(gulp.dest('build/web/static/favicon'));

    done();
});

function watchFiles() {
  gulp.watch(paths.js.watchFiles, gulp.series("js"));
  gulp.watch(paths.css.watchFiles, gulp.series("css"));
}

gulp.task("watch", gulp.series(watchFiles), (done) => done());
gulp.task("default", gulp.series("css", "js", "images", "favicons"), (done) => done());
