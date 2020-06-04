const {
  dest,
  parallel,
  src,
  pipe,
  watch
} = require('gulp');

const sourcemaps = require('gulp-sourcemaps');

exports.css = function() {
  const postcss = require('gulp-postcss');
  const url = require('postcss-url');

  const plugins = [
        require('precss'),
        require('autoprefixer'),
        require('postcss-import'),
        url({url: "inline"}), // Inline font URLs in our CSS
        require('cssnano')
  ];


    return src('web/src/**/*.css')
    .pipe(sourcemaps.init())
    .pipe(postcss(plugins))
    // sourcemaps are rooted in dest(), so '.' is what we want
    .pipe(sourcemaps.write('.'))
    .pipe( dest('build/web/static') );
};

exports.js = function() {

  const babel = require('gulp-babel');
  const uglify = require('gulp-uglify');
  const concat = require('gulp-concat');
  const webpack = require('webpack-stream');
  const named = require('vinyl-named');

    return src('web/src/js/app.js')
    .pipe(named())
    .pipe(babel())
    .pipe(webpack({
      devtool: 'source-map',
      output: {
        filename: 'main.js',
      },
    }))
    // sourcemaps are rooted in dest(), so '.' is what we want
    .pipe(sourcemaps.write('.'))
    .pipe(dest('build/web/static/js'));
};

exports.images = function () {
    return src('web/src/images/*')
    .pipe(dest('build/web/static/images'))
};

exports.favicons = function () {
    return src('web/src/favicon/*')
    .pipe(dest('build/web/static/favicon'))
};

exports.default = parallel(exports.css, exports.js, exports.images, exports.favicons);

exports.watch = function() {
    watch('web/src/**/*.css', {ignoreInitial: false}, exports.css);
    watch('web/src/**/*.js', {ignoreInitial: false}, exports.js);
    watch('web/src/**/*.svg', {ignoreInitial: false}, exports.images);
};
