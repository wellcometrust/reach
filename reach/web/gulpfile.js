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


  return src('static/**/*.css')
    .pipe(sourcemaps.init())
    .pipe(postcss(plugins))
    // sourcemaps are rooted in dest(), so '.' is what we want
    .pipe(sourcemaps.write('.'))
    .pipe( dest('/opt/reach/build/web/static') );
};

exports.js = function() {

  const babel = require('gulp-babel');
  const uglify = require('gulp-uglify');
  const concat = require('gulp-concat')

  return src('static/**/*.js')
    .pipe(concat('main.js'))
    .pipe(sourcemaps.init())
    .pipe(babel())
    .pipe(uglify())
    // sourcemaps are rooted in dest(), so '.' is what we want
    .pipe( sourcemaps.write('.') )
    .pipe( dest('/opt/reach/build/web/static') );
};

exports.default = parallel(exports.css, exports.js);

exports.watch = function() {
  watch('src/*.css', {ignoreInitial: false}, exports.css);
  watch('src/*.js', {ignoreInitial: false}, exports.js);
};
