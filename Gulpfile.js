var gulp = require("gulp"),
    $ = require("gulp-load-plugins")(),
    sprite = require("sprity"),
    path = require("path"),
    del = require("del");

var sourceDir = "assets",
    destDir = "dist",
    errorsDir = "errors",
    sassDir = "scss",
    cssDir = "css",
    imagesDir = "images",
    scriptsDir = "js",
    vendorsDir = "vendors",
    spriteDir = "sprite",
    stylesFiles = ["main.scss", "only-ie.scss"],
    vendorsCSS = ["node_modules/normalize.css/normalize.css"],
    vendorsJS = ["node_modules/jquery/dist/jquery.js", "node_modules/cookies-eu-banner/dist/cookies-eu-banner.js"],
    autoprefixerConfig = ["last 1 version", "> 1%", "ff >= 20", "ie >= 8", "opera >= 12", "Android >= 2.2"],
    imageminConfig = { optimizationLevel: 3, progressive: true, interlaced: true };

/**
 * Cleans up the workspace, deletes the build
 */
gulp.task("clean", function(cb) {
  del([
    destDir,
    path.join(sourceDir, "{" + scriptsDir + "," + sassDir + "}", vendorsDir),
    path.join(sourceDir, "bower_components/"),
    path.join(sourceDir, sassDir, "_sprite.scss")
   ], cb);
});

/**
 * Clean error-pages files
 */
gulp.task("clean-errors", function(cb) {
  del(["errors/css/*"], cb);
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
    .pipe($.concat("vendors.js"))
    .pipe($.size({ title: "Scripts (vendors)" }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)))
    .pipe($.rename({ suffix: ".min" }))
    .pipe($.size({ title: "Scripts (vendors, minified)" }))
    .pipe($.uglify().on('error', $.notify.onError({
      title: "Javascript error",
      message: "<%= error.message %>"
    })))
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
      .pipe($.sass({
        sourceMapContents: true,
        outputStyle: "compressed"
      }))
        .on("error", $.notify.onError({
            title: "SASS Error",
            message: "<%= error.message %>"
        }))
        .on("error", function() { this.emit("end"); })
      .pipe($.autoprefixer(autoprefixerConfig, { cascade: true }))
    .pipe($.sourcemaps.write('.', { sourceRoot: "../../assets/scss/" }))
    .pipe($.size({ title: "Stylesheet" }))
    .pipe(gulp.dest(path.join(destDir, cssDir)));
});

/**
 * Error-pages stylesheet
 */
gulp.task("errors", ["clean-errors"], function() {
  return gulp.src(path.join(errorsDir, sassDir, "main.scss"))
    .pipe($.sourcemaps.init())
      .pipe($.sass({
        includePaths: [path.join(sourceDir, sassDir)],
        sourceMapContents: true,
        outputStyle: "compressed"
      }))
      .pipe($.autoprefixer(autoprefixerConfig, { cascade: true }))
    .pipe($.sourcemaps.write(".", { sourceRoot: "../../errors/scss/" }))
    .pipe(gulp.dest(path.join(errorsDir, cssDir)));
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
    .pipe($.concat("main.js", { newLine: "\r\n\r\n" }))
    .pipe($.size({ title: "Scripts" }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)))
    .pipe($.rename({ suffix: ".min" }))
    .pipe($.uglify().on('error', $.notify.onError({
      title: "Javascript error",
      message: "<%= error.message %>"
    })))
    .pipe($.size({ title: "Scripts (minified)" }))
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
  return gulp.src(path.join(destDir, scriptsDir, "{vendors,main}.js"))
    .pipe($.concat("all.js"))
    .pipe($.size({ title: "Scripts (all)" }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)))
    .pipe($.rename({ suffix: ".min" }))
    .pipe($.uglify().on('error', $.notify.onError({
      title: "Javascript error",
      message: "<%= error.message %>"
    })))
    .pipe($.size({ title: "Scripts (all, minified)" }))
    .pipe(gulp.dest(path.join(destDir, scriptsDir)));
});

/**
 * Watch for files changes, then recompiles and livereloads
 */
gulp.task("watch", function() {
  gulp.watch(path.join(sourceDir, scriptsDir, "*.js"), ["jshint", "scripts"]);
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
