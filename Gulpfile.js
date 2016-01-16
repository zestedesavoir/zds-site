var gulp = require("gulp"),
    $ = require("gulp-load-plugins")(),
    sprite = require("sprity"),
    path = require("path"),
    del = require("del");

var postcssProcessors = [
  require("postcss-import"), // Must be first
  require("postcss-advanced-variables"),
  require("postcss-atroot"),
  require("postcss-calc"),
  require("postcss-color-function"),
  require("postcss-custom-media"),
  require("postcss-mixins"),
  require("postcss-nested"),
  require("postcss-nesting"),
  require("autoprefixer")({ browsers: ["last 1 version", "> 1%", "ff >= 20", "ie >= 8", "opera >= 12", "Android >= 2.2"] }),
  //require("cssnano")({ discardComments: { removeAll: true }})
];

var sourceDir = "assets",
    destDir = "dist",
    errorsDir = "errors",
    cssDir = "css",
    imagesDir = "images",
    scriptsDir = "js",
    spriteDir = "sprite",
    stylesFiles = ["main.css"],
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
    .pipe($.sourcemaps.init())
      .pipe($.concat("vendors.js"))
      .pipe($.uglify().on('error', $.notify.onError({
        title: "Javascript error",
        message: "<%= error.message %>"
      })))
    .pipe($.sourcemaps.write(".", { includeContent: true }))
    .pipe($.size({ title: "Scripts (vendors)" }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)));
});

/**
 * Compiles SASS files
 */
gulp.task("stylesheet", ["sprite"], function() {
  var files = stylesFiles.map(function(filename) {
    return path.join(sourceDir, cssDir, filename);
  });

  return gulp.src(files)
    .pipe($.sourcemaps.init())
      .pipe($.postcss(postcssProcessors))
    .pipe($.sourcemaps.write(".", { includeContent: true, sourceRoot: path.join("../../", sourceDir, cssDir) }))
    .on("error", function() { this.emit("end"); })
    .pipe($.size({ title: "Stylesheet" }))
    .pipe(gulp.dest(path.join(destDir, "css/")));
});

/**
 * Error-pages stylesheet
 */
gulp.task("errors", ["clean-errors"], function() {
  return gulp.src(path.join(errorsDir, cssDir, "main.css"))
    .pipe($.sourcemaps.init())
      .pipe($.postcss(postcssProcessors))
    .pipe($.sourcemaps.write(".", { includeContent: true }))
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
    .pipe($.if("*.png", $.imagemin(imageminConfig)))
    .pipe($.if("*.png", gulp.dest(path.join(destDir, imagesDir)), gulp.dest(path.join(sourceDir, cssDir))));
});

/**
 * Process images files
 */
gulp.task("images",  ["stylesheet"], function() {
  return gulp.src(path.join(sourceDir, "{" + imagesDir + ",smileys}", "*.{jpg,png,gif}"))
    .pipe($.imagemin(imageminConfig))
    .pipe($.size({ title: "Images" }))
    .pipe(gulp.dest(destDir));
});

/**
 * Scripts concat and minify
 */
gulp.task("scripts", function() {
  return gulp.src(path.join(sourceDir, scriptsDir, "*.js"))
    .pipe($.sourcemaps.init())
      .pipe($.concat("main.js", { newLine: "\r\n\r\n" }))
      .pipe($.uglify().on('error', $.notify.onError({
        title: "Javascript error",
        message: "<%= error.message %>"
      })))
    .pipe($.sourcemaps.write(".", { includeContent: true, sourceRoot: path.join("../../", sourceDir, scriptsDir) }))
    .pipe($.size({ title: "Scripts" }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)));
});

/**
 * Check JS code style and syntax using JSHint
 */
gulp.task("jshint", function() {
  return gulp.src([path.join(sourceDir, scriptsDir, "*.js"), "!" + path.join(sourceDir, scriptsDir, "_custom.modernizr.js")])
    .pipe($.jshint())
    .pipe($.jshint.reporter("jshint-stylish"));
});

/**
 * Merge vendors and app scripts
 */
gulp.task("merge-scripts", ["vendors", "scripts"], function() {
  return gulp.src([path.join(destDir, scriptsDir, "vendors.js"), path.join(destDir, scriptsDir, "main.js")])
    .pipe($.sourcemaps.init({ loadMaps: true }))
      .pipe($.concat("all.js"))
    .pipe($.sourcemaps.write(".", { includeContent: true, sourceRoot: path.join("../../", sourceDir, scriptsDir) }))
    .pipe($.size({ title: "Scripts (all)" }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)));
});

/**
 * Watch for files changes, then recompiles and livereloads
 */
gulp.task("watch", function() {
  gulp.watch(path.join(sourceDir, scriptsDir, "*.js"), ["jshint", "scripts"]);
  gulp.watch([path.join(sourceDir, imagesDir, "*.png"), path.join(sourceDir, "smileys/*")], ["images"]);
  gulp.watch([path.join(sourceDir, cssDir, "**/*.css"), "!" + path.join(sourceDir, cssDir, "_sprite.css")], ["stylesheet"]);

  gulp.watch("dist/*/**", function(file) {
    var filePath = path.join("static/", path.relative(path.join(__dirname, "dist/"), file.path)); // Pour que le chemin ressemble à static/.../...
    $.livereload.changed(filePath);
  });

  $.livereload.listen();
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
