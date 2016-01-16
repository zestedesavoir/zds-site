var gulp = require("gulp"),
    concat = require("gulp-concat"),
    del = require("del"),
    gulpIf = require("gulp-if"),
    imagemin = require("gulp-imagemin"),
    jshint = require("gulp-jshint"),
    livereload = require("gulp-livereload"),
    newer = require("gulp-newer"),
    notify = require("gulp-notify"),
    path = require("path"),
    postcss = require("gulp-postcss"),
    rename = require("gulp-rename"),
    sourcemaps = require("gulp-sourcemaps"),
    sprite = require("sprity"),
    uglify = require("gulp-uglify");

var postcssProcessors = [
  require("postcss-import"), // Must be first
  require("postcss-advanced-variables"),
  require("postcss-calc"),
  require("postcss-color-function"),
  require("postcss-custom-media"),
  require("postcss-mixins"),
  require("postcss-nested"),
  require("autoprefixer")({ browsers: ["last 1 version", "> 1%", "ie >= 10"] }),
  require("cssnano")({ discardComments: { removeAll: true }})
];

var sourceDir = "assets",
    destDir = "dist",
    errorsDir = "errors",
    cssDir = "css",
    imagesDir = "images",
    scriptsDir = "js",
    spriteDir = "sprite",
    vendorsJS = ["node_modules/jquery/dist/jquery.js", "node_modules/cookies-eu-banner/dist/cookies-eu-banner.js"],
    imageminConfig = { optimizationLevel: 3, progressive: true, interlaced: true };

/**
 * Cleans up the workspace, deletes the build
 */
gulp.task("clean", function() {
  return del([
    destDir,
    path.join(sourceDir, "sass/"),
    path.join(sourceDir, scriptsDir, "vendors/"),
    path.join(sourceDir, "bower_components/"),
    path.join(sourceDir, cssDir, "sprite.css")
   ]);
});

/**
 * Clean error-pages files
 */
gulp.task("clean-errors", function() {
  return del(["errors/css/*"]);
});

/**
 * Copy, concat and minify vendors files
 */
gulp.task("vendors", function() {
  return gulp.src(vendorsJS)
    .pipe(newer(path.join(destDir, scriptsDir, "vendors.js")))
    .pipe(sourcemaps.init())
      .pipe(concat("vendors.js"))
      .pipe(uglify().on('error', notify.onError({
        title: "Javascript error",
        message: "<%= error.message %>"
      })))
    .pipe(sourcemaps.write(".", { includeContent: true }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)));
});

/**
 * Compiles SASS files
 */
gulp.task("stylesheet", ["sprite"], function() {
  return gulp.src(path.join(sourceDir, cssDir, "main.css"))
    .pipe(newer(path.join(destDir, cssDir)))
    .pipe(sourcemaps.init())
      .pipe(postcss(postcssProcessors))
    .pipe(sourcemaps.write(".", { includeContent: true, sourceRoot: path.join("../../", sourceDir, cssDir) }))
    .on("error", function() { this.emit("end"); })
    .pipe(gulp.dest(path.join(destDir, "css/")));
});

/**
 * Error-pages stylesheet
 */
gulp.task("errors", ["clean-errors"], function() {
  return gulp.src(path.join(sourceDir, cssDir, "errors.css"))
    .pipe(sourcemaps.init())
      .pipe(postcss(postcssProcessors))
    .pipe(sourcemaps.write(".", { includeContent: true }))
    .pipe(gulp.dest(path.join(errorsDir, "css/")));
});

/**
 * Generates Sprite files (SASS + image)
 */
gulp.task("sprite", function() {
  return sprite.src({
      cssPath: "../" + imagesDir + "/",
      dimension: [{ ratio: 1, dpi: 72 },
                  { ratio: 2, dpi: 192 }],
      margin: 0,
      src: path.join(sourceDir, imagesDir, spriteDir, "*"),
      style: "sprite.css",
      template: path.join(sourceDir, cssDir, "sprite-template.hbs")
    })
    .pipe(gulpIf("*.png", imagemin(imageminConfig)))
    .pipe(gulpIf("*.png", gulp.dest(path.join(destDir, imagesDir)), gulp.dest(path.join(sourceDir, cssDir))));
});

/**
 * Process images files
 */
gulp.task("images",  ["stylesheet"], function() {
  return gulp.src(path.join(sourceDir, "{" + imagesDir + ",smileys}", "*.{jpg,png,gif}"))
    .pipe(newer(destDir))
    .pipe(imagemin(imageminConfig))
    .pipe(gulp.dest(destDir));
});

/**
 * Scripts concat and minify
 */
gulp.task("scripts", function() {
  return gulp.src(path.join(sourceDir, scriptsDir, "*.js"))
    .pipe(newer(path.join(destDir, scriptsDir, "main.js")))
    .pipe(sourcemaps.init())
      .pipe(concat("main.js", { newLine: "\r\n\r\n" }))
      .pipe(uglify().on('error', notify.onError({
        title: "Javascript error",
        message: "<%= error.message %>"
      })))
    .pipe(sourcemaps.write(".", { includeContent: true, sourceRoot: path.join("../../", sourceDir, scriptsDir) }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)));
});

/**
 * Check JS code style and syntax using JSHint
 */
gulp.task("jshint", function() {
  return gulp.src([path.join(sourceDir, scriptsDir, "*.js"), "!" + path.join(sourceDir, scriptsDir, "_custom.modernizr.js")])
    .pipe(jshint())
    .pipe(jshint.reporter("jshint-stylish"));
});

/**
 * Merge vendors and app scripts
 */
gulp.task("merge-scripts", ["vendors", "scripts"], function() {
  return gulp.src([path.join(destDir, scriptsDir, "vendors.js"), path.join(destDir, scriptsDir, "main.js")])
    .pipe(newer(path.join(destDir, scriptsDir, "all.js")))
    .pipe(sourcemaps.init({ loadMaps: true }))
      .pipe(concat("all.js"))
    .pipe(sourcemaps.write(".", { includeContent: true, sourceRoot: path.join("../../", sourceDir, scriptsDir) }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)));
});

/**
 * Watch for files changes, then recompiles and livereloads
 */
gulp.task("watch", function() {
  gulp.watch(path.join(sourceDir, scriptsDir, "*.js"), ["jshint", "scripts"]);
  gulp.watch([path.join(sourceDir, imagesDir, "*.png"), path.join(sourceDir, "smileys/*")], ["images"]);
  gulp.watch([path.join(sourceDir, cssDir, "**/*.css"), "!" + path.join(sourceDir, cssDir, "sprite.css")], ["stylesheet"]);

  gulp.watch("dist/*/**", function(file) {
    var filePath = path.join("static/", path.relative(path.join(__dirname, "dist/"), file.path)); // Pour que le chemin ressemble à static/.../...
    livereload.changed(filePath);
  });

  livereload.listen();
});

/**
 * Tests
 */
gulp.task("test", ["jshint"]);

/**
 * CI builds
 */
gulp.task("travis", ["test", "build"]);

/**
 * Build all the things!
 */
gulp.task("build", ["images", "sprite", "stylesheet", "merge-scripts"]);

/**
 * Default task: build and watch
 */
gulp.task("default", ["build", "watch"]);
