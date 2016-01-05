var gulp = require("gulp"),
    $ = require("gulp-load-plugins")(),
    sprite = require("sprity"),
    path = require("path"),
    del = require("del");

var autoprefixer = require("autoprefixer"),
    cssnano = require("cssnano");

var postcssProcessors = [
  require("autoprefixer")({ browsers: ["last 1 version", "> 1%", "ff >= 20", "ie >= 8", "opera >= 12", "Android >= 2.2"] }),
  require("cssnano")()
];

var sourceDir = "assets",
    destDir = "dist",
    errorsDir = "errors",
    sassDir = "scss",
    imagesDir = "images",
    scriptsDir = "js",
    vendorsDir = "vendors",
    spriteDir = "sprite",
    stylesFiles = ["main.scss"],
    vendorsCSS = ["node_modules/normalize.css/normalize.css", "node_modules/pikaday/css/pickaday.css", "node_modules/pikaday/css/theme.css"],
    vendorsJS = ["node_modules/jquery/dist/jquery.js", "node_modules/cookies-eu-banner/dist/cookies-eu-banner.js", "node_modules/pikaday/pikaday.js"],
    imageminConfig = { optimizationLevel: 3, progressive: true, interlaced: true };

/**
 * Cleans up the workspace, deletes the build
 */
gulp.task("clean", function() {
  return del([
    destDir,
    path.join(sourceDir, "{" + scriptsDir + "," + sassDir + "}", vendorsDir),
    path.join(sourceDir, "bower_components/"),
    path.join(sourceDir, sassDir, "_sprite.scss")
   ]);
});

/**
 * Clean error-pages files
 */
gulp.task("clean-errors", function() {
  return del(["errors/css/*"]);
});

/**
 * Copy vendors style files (i.e. normalize.css)
 */
gulp.task("vendors-css", function() {
  return gulp.src(vendorsCSS)
    .pipe($.rename({ prefix: "_", extname: ".scss" }))
    .pipe(gulp.dest(path.join(sourceDir, sassDir, vendorsDir)));
});

/**
 * Copy vendors script fules (i.e. jquery.js)
 */
gulp.task("vendors-js", function() {
  return gulp.src(vendorsJS)
    .pipe(gulp.dest(path.join(sourceDir, scriptsDir, vendorsDir)));
});

/**
 * Copy, concat and minify vendors files
 */
gulp.task("vendors", ["vendors-js", "vendors-css"], function() {
  return gulp.src(path.join(sourceDir, scriptsDir, vendorsDir, "*.js"))
    .pipe($.sourcemaps.init())
      .pipe($.concat("vendors.js"))
      .pipe($.uglify().on('error', $.notify.onError({
        title: "Javascript error",
        message: "<%= error.message %>"
      })))
    .pipe($.sourcemaps.write(".", { includeContent: true, sourceRoot: path.join("../../", vendorsDir) }))
    .pipe($.size({ title: "Scripts (vendors)" }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)));
});

/**
 * Compiles SASS files
 */
gulp.task("stylesheet", ["sprite", "vendors"], function() {
  var files = stylesFiles.map(function(filename) {
    return path.join(sourceDir, sassDir, filename);
  });

  return gulp.src(files)
    .pipe($.sourcemaps.init())
      .pipe($.sass({ sourceMapContents: true }))
      .on("error", $.notify.onError({
        title: "SASS Error",
        message: "<%= error.message %>"
      }))
      .pipe($.postcss(postcssProcessors))
    .pipe($.sourcemaps.write(".", { includeContent: true, sourceRoot: path.join("../../", sourceDir, sassDir) }))
    .on("error", function() { this.emit("end"); })
    .pipe($.size({ title: "Stylesheet" }))
    .pipe(gulp.dest(path.join(destDir, "css/")));
});

/**
 * Error-pages stylesheet
 */
gulp.task("errors", ["clean-errors"], function() {
  return gulp.src(path.join(errorsDir, sassDir, "main.scss"))
    .pipe($.sourcemaps.init())
      .pipe($.sass({
        includePaths: [path.join(sourceDir, sassDir)]
      }))
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
      style: "_sprite.scss",
      template: path.join(sourceDir, sassDir, "sprite-template.hbs")
    })
    .pipe($.if("*.png", $.imagemin(imageminConfig)))
    .pipe($.if("*.png", gulp.dest(path.join(destDir, imagesDir)), gulp.dest(path.join(sourceDir, sassDir))));
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
  gulp.watch(path.join(sourceDir, scriptsDir, "*.js"), ["jshint", "merge-scripts"]);
  gulp.watch([path.join(sourceDir, imagesDir, "*.png"), path.join(sourceDir, "smileys/*")], ["images"]);
  gulp.watch([path.join(sourceDir, sassDir, "**/*.scss"), "!" + path.join(sourceDir, sassDir, "_sprite.scss")], ["stylesheet"]);

  gulp.watch("dist/*/**", function(file) {
    var filePath = path.join("static/", path.relative(path.join(__dirname, "dist/"), file.path)); // Pour que le chemin ressemble à static/.../...
    $.livereload.changed(filePath);
  });

  $.livereload.listen();
});

/**
 * Tests
 */
gulp.task("lint", ["jshint"]);

/**
 * CI builds
 */
gulp.task("travis", ["lint", "build"]);

/**
 * Build all the things!
 */
gulp.task("build", ["images", "sprite", "stylesheet", "merge-scripts"]);

/**
 * Default task: build and watch
 */
gulp.task("default", ["build", "watch"]);
