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


  return src('src/**/*.css')
    .pipe(sourcemaps.init())
    .pipe(postcss(plugins))
    // sourcemaps are rooted in dest(), so '.' is what we want
    .pipe(sourcemaps.write('.'))
    .pipe( dest('/opt/reach/build/web/static') );
};

exports.js = function() {

  const babel = require('gulp-babel');
  const uglify = require('gulp-uglify');
  const concat = require('gulp-concat');
  const webpack = require('webpack-stream');
  const named = require('vinyl-named');

  return src('src/js/app.js')
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
    .pipe(dest('/opt/reach/build/web/static/js'));
};

exports.images = function () {
  return src('src/images/*')
    .pipe(dest('/opt/reach/build/web/static/images'))
};

exports.default = parallel(exports.css, exports.js, exports.images);

exports.watch = function() {
  watch('src/**/*.css', {ignoreInitial: false}, exports.css);
  watch('src/**/*.js', {ignoreInitial: false}, exports.js);
  watch('src/**/*.svg', {ignoreInitial: false}, exports.images);
};
