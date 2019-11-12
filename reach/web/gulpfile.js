const {
  dest,
  parallel,
  src,
  pipe,
  watch
} = require('gulp');

exports.css = function() {
  const postcss = require('gulp-postcss');
  const sourcemaps = require('gulp-sourcemaps');
  const url = require('postcss-url');

  const plugins = [
        require('precss'),
        require('autoprefixer'),
        require('postcss-import'),
        url({url: "inline"}), // Inline font URLs in our CSS
        require('cssnano')
  ];

  return src('src/**/*.css')
    .pipe( sourcemaps.init() )
    .pipe( postcss(plugins) )
    // sourcemaps are rooted in dest(), so '.' is what we want
    .pipe( sourcemaps.write('.') )
    .pipe( dest('/opt/reach/build/web/static') );
};

exports.default = parallel(exports.css);

exports.watch = function() {
  watch('src/*.css', {ignoreInitial: false}, exports.css);
};
