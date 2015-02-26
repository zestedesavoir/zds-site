var gulp = require("gulp"),
    $ = require("gulp-load-plugins")(),
    browserify = require("browserify"),
    watchify = require("watchify"),
    source = require("vinyl-source-stream"),
    sprite = require("css-sprite").stream,
    path = require("path"),
    del = require("del");

var sourceDir = "assets/",
    destDir = "dist/",
    appFile = "js/app.js"
    styleFile = "main.scss",
    sassDir = "scss/",
    imagesDir = "images/",
    scriptsDir = "js/",
    vendorsDir = "vendors/",
    spriteDir = "sprite/",
    vendorsCSS = ["node_modules/normalize.css/normalize.css"],
    vendorsJS = ["node_modules/jquery/dist/jquery.js"],
    autoprefixerConfig = ["last 1 version", "> 1%", "ff >= 20", "ie >= 8", "opera >= 12", "Android >= 2.2"]
    imageminConfig = { optimizationLevel: 3, progressive: true, interlaced: true };

/**
 * Cleans up the workspace, deletes the build
 */
gulp.task("clean", function(cb) {
  del([
    destDir,
    sourceDir + "{" + scriptsDir + "," + sassDir + "}/" + vendorsDir,
    sourceDir + "bower_components/",
    sourceDir + sassDir + "_sprite.scss"
   ], cb);
});

/**
 * Clean error-pages files
 */
gulp.task("clean-errors", function(cb) {
  del(["errors/css/*"], cb);
});

/**
 * Bundles JS files using browserify (unused yet)
 */
gulp.task("bundle", function() {
  var bundler = watchify(browserify({
    entries: ["./" + sourceDir + appFile],
    insertGlobals: true,
    cache: {},
    packageCache: {},
    fullpaths: true
  }));

  bundler.on("update", rebundle);

  function rebundle() {
    return bundler.bundle()
      .on("error", $.notify.onError({
        title: "Browserify error",
        message: "<%= error.message %>"
      }))
      .pipe(source(appFile))
      .pipe($.streamify($.size({ title: "App file" })))
      .pipe(gulp.dest(destDir))
      .pipe($.rename({ suffix: ".min" }))
      .pipe($.streamify($.uglify().on('error', $.notify.onError({
        title: "Javascript error",
        message: "<%= error.message %>"
      }))))
      .pipe($.streamify($.size({ title: "App file (minified)" })))
      .pipe(gulp.dest(destDir));
  }

  return rebundle();
});

/**
 * Copy vendors style files (i.e. normalize.css)
 */
gulp.task("vendors-css", function() {
  return gulp.src(vendorsCSS)
    .pipe($.rename({ prefix: "_", extname: ".scss" }))
    .pipe(gulp.dest(sourceDir + sassDir + vendorsDir));
});

/**
 * Copy vendors script fules (i.e. jquery.js)
 */
gulp.task("vendors-js", function() {
  return gulp.src(vendorsJS)
    .pipe(gulp.dest(sourceDir + scriptsDir + vendorsDir));
});

/**
 * Copy, concat and minify vendors files
 */
gulp.task("vendors", ["vendors-js", "vendors-css"], function() {
  return gulp.src(sourceDir + scriptsDir + vendorsDir + "*.js")
    .pipe($.concat("vendors.js"))
    .pipe($.size({ title: "Scripts (vendors)" }))
    .pipe(gulp.dest(destDir + scriptsDir))
    .pipe($.rename({ suffix: ".min" }))
    .pipe($.size({ title: "Scripts (vendors, minified)" }))
    .pipe($.uglify().on('error', $.notify.onError({
      title: "Javascript error",
      message: "<%= error.message %>"
    })))
    .pipe(gulp.dest(destDir + scriptsDir));
});

/**
 * Compiles SASS files
 */
gulp.task("stylesheet", ["sprite", "vendors"], function() {
  return gulp.src(sourceDir + sassDir + styleFile)
    .pipe($.sass({
      sass: sourceDir + sassDir,
      imagePath: sourceDir + imagesDir
    }))
    .on("error", $.notify.onError({
      title: "SASS Error",
      message: "<%= error.message %>"
    }))
    .on("error", function() { this.emit("end"); })
    .pipe($.autoprefixer(autoprefixerConfig, { cascade: true }))
    .pipe($.size({ title: "Stylesheet" }))
    .pipe(gulp.dest(destDir + "css/"))
    .pipe($.rename({ suffix: ".min" }))
    .pipe($.minifyCss())
    .pipe($.size({ title: "Stylesheet (minified)" }))
    .pipe(gulp.dest(destDir + "css/"));
});

/**
 * Error-pages stylesheet
 */
gulp.task("errors", ["clean-errors"], function() {
  return gulp.src(errorsDir + sassDir + styleFile)
    .pipe($.sass({
      sass: errorsDir + sassDir,
      imagePath: errorsDir + imagesDir,
      includePaths: [sourceDir + imagesDir]
    }))
    .pipe($.autoprefixer(autoprefixerConfig, { cascade: true }))
    .pipe(gulp.dest(errorsDir + "css/"))
    .pipe($.rename({ suffix: ".min" }))
    .pipe($.minifyCss())
    .pipe(gulp.dest(errorsDir + "css/"));
});

/**
 * Generates Sprite files (SASS + image)
 */
gulp.task("sprite", function() {
  return gulp.src(sourceDir + imagesDir + spriteDir + "*")
    .pipe(sprite({
      name: "sprite",
      style: "_sprite.scss",
      cssPath: "../images",
      retina: true,
      prefix: "sprite-icon",
      processor: "scss",
      template: sourceDir + sassDir + "sprite-template.mustache"
    }))
    .pipe($.if("*.png", gulp.dest(destDir + imagesDir), gulp.dest(sourceDir + sassDir)));
});

/**
 * Process images files
 */
gulp.task("images",  ["stylesheet"], function() {
  return gulp.src([sourceDir + "{" + imagesDir + ",smileys/}" + "*.{png,gif}"])
    .pipe($.imagemin(imageminConfig))
    .pipe($.size({ title: "Images" }))
    .pipe(gulp.dest(destDir));
});

/**
 * Scripts concat and minify
 */
gulp.task("scripts", function() {
  return gulp.src(sourceDir + scriptsDir + "*.js")
    .pipe($.concat("main.js", { newLine: "\r\n\r\n" }))
    .pipe($.size({ title: "Scripts" }))
    .pipe(gulp.dest(destDir + scriptsDir))
    .pipe($.rename({ suffix: ".min" }))
    .pipe($.uglify().on('error', $.notify.onError({
      title: "Javascript error",
      message: "<%= error.message %>"
    })))
    .pipe($.size({ title: "Scripts (minified)" }))
    .pipe(gulp.dest(destDir + scriptsDir));
});

/**
 * Check JS code style and syntax using JSHint
 */
gulp.task("jshint", function() {
  return gulp.src([sourceDir + scriptsDir + "*.js", "!" + sourceDir + scriptsDir + "_custom.modernizr.js"])
    .pipe($.jshint())
    .pipe($.jshint.reporter("jshint-stylish"));
});

/**
 * Merge vendors and app scripts
 */
gulp.task("merge-scripts", ["vendors", "scripts"], function() {
  return gulp.src([destDir + scriptsDir + "vendors.js", destDir + scriptsDir + "main.js"])
    .pipe($.concat("all.js"))
    .pipe($.size({ title: "Scripts (all)" }))
    .pipe(gulp.dest(destDir + scriptsDir))
    .pipe($.rename({ suffix: ".min" }))
    .pipe($.uglify().on('error', $.notify.onError({
      title: "Javascript error",
      message: "<%= error.message %>"
    })))
    .pipe($.size({ title: "Scripts (all, minified)" }))
    .pipe(gulp.dest(destDir + scriptsDir));
});

/**
 * Watch for files changes, then recompiles and livereloads
 */
gulp.task("watch", function() {
  gulp.watch(sourceDir + scriptsDir + "*.js", ["jshint", "scripts"]);
  gulp.watch([sourceDir + imagesDir + "*.png", sourceDir + "smileys/*"], ["images"]);
  gulp.watch([sourceDir + sassDir + "**/*.scss", "!" + sourceDir + sassDir + "_sprite.scss"], ["stylesheet"]);

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
