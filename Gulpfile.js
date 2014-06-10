var gulp = require("gulp"),
    $ = require("gulp-load-plugins")(),
    path = require("path"),
    spritesmith = require("gulp.spritesmith");

var paths = {
  scripts: "assets/js/**",
  images: "assets/images/**",
  smileys: "assets/smileys/**",
  copy: "assets/misc/**",
  stylesheet: "assets/scss/main.scss",
  scss: ["assets/scss/**", "!assets/scss/_sprite.scss"],
  sass: {
    sass: "assets/scss",
    images: "assets/images",
    includePaths: ["assets/scss"],
  },
  sprite: "assets/images/sprite@2x/*.png"
};

gulp.task("clean", function() {
  return gulp.src(["dist/*"])
    .pipe($.clean());
});

gulp.task("script", ["test"], function() {
  return gulp.src(paths.scripts)
    .pipe($.newer("dist/js/main.js"))
    .pipe($.concat("main.js", { newLine: "\r\n\r\n" }))
    .pipe(gulp.dest("dist/js"))
    .pipe($.size({ title: "main.js" }))
    .pipe($.rename({ suffix: ".min" }))
    .pipe($.uglify())
    .pipe(gulp.dest("dist/js"))
    .pipe($.size({ title: "main.min.js" }));
});

gulp.task("stylesheet", ["sprite"], function() {
  return gulp.src(paths.stylesheet)
    .pipe($.sass({
      sass: paths.sass.sass,
      imagePath: paths.sass.images,
      includePaths: paths.sass.includePaths
    }))
    .pipe($.autoprefixer(["last 1 version", "> 1%", "ff >= 20", "ie >= 8", "opera >= 12", "Android >= 2.2"], { cascade: true }))
    .pipe(gulp.dest("dist/css"))
    .pipe($.rename({ suffix: ".min" })) // génère une version minimifié
    .pipe($.minifyCss())
    .pipe(gulp.dest("dist/css"));
});

gulp.task("sprite", function() {
  var sprite = gulp.src(paths.sprite)
    .pipe(spritesmith({
      imgName: "sprite@2x.png",
      cssName: "_sprite.scss",
      cssTemplate: function(params) {
        var output = "", e;
        for(var i in params.items) {
          e = params.items[i];
          output += "$" + e.name + ": " + e.px.offset_x + " " + e.px.offset_y + ";\n";
        }
        if(params.items.length > 0) {
          output += "\n\n";
          output += "$sprite_height: " + params.items[0].px.total_height + ";\n";
          output += "$sprite_width: " + params.items[0].px.total_width + ";";
        }

        return output;
      }
    }));
  sprite.img.pipe(gulp.dest("dist/images"));
  sprite.css.pipe(gulp.dest(paths.sass.sass));
  return sprite.css;
});

gulp.task("images", ["stylesheet"], function() {
  return gulp.src(paths.images)
    .pipe($.newer("dist/images"))
    .pipe($.cache($.imagemin({ optimizationLevel: 3, progressive: true, interlaced: true })))
    .pipe($.size())
    .pipe(gulp.dest("dist/images"));
});

gulp.task("smileys", function() {
  return gulp.src(paths.smileys)
    .pipe($.newer("dist/smileys"))
    .pipe($.cache($.imagemin({ optimizationLevel: 3, progressive: true, interlaced: true })))
    .pipe($.size())
    .pipe(gulp.dest("dist/smileys"));
});

gulp.task("vendors", function() {
  return $.bowerFiles()
    .pipe($.newer("dist/js/vendors.js"))
    .pipe($.flatten()) // remove folder structure
    .pipe($.size({ title: "vendors", showFiles: true }))
    .pipe(gulp.dest("dist/js/vendors"))
    .pipe($.concat("vendors.js"))
    .pipe($.size({ title: "vendors.js" }))
    .pipe(gulp.dest("dist/js"))
    .pipe($.uglify())
    .pipe($.rename("vendors.min.js"))
    .pipe($.size({ title: "vendors.min.js" }))
    .pipe(gulp.dest("dist/js"));
});

gulp.task("merge-scripts", ["script", "vendors"], function() {
  return gulp.src("dist/js/{vendors,main}.min.js")
    .pipe($.concat("all.min.js"))
    .pipe($.size())
    .pipe(gulp.dest("dist/js/"));
});

gulp.task("watch", function(cb) {
  gulp.watch(paths.script, ["script"]);
  gulp.watch(paths.copy, ["copy"]);
  gulp.watch(paths.smiley, ["smileys"]);
  gulp.watch(paths.images, ["images"]);
  gulp.watch(paths.scss, ["stylesheet"]);
  gulp.watch(paths.sprite, ["sprite", "stylesheet"]);

  gulp.watch("dist/*/**", function(file) {
    filePath = path.join("static/", path.relative(path.join(__dirname, "dist/"), file.path)); // Pour que le chemin ressemble à static/.../...
    $.livereload.changed(filePath);
  });

  $.livereload.listen();
});

gulp.task("test", function() {
  return gulp.src(paths.scripts)
    .pipe($.jshint())
    .pipe($.jshint.reporter("jshint-stylish"));
});

gulp.task("copy", function() {
  return gulp.src(paths.copy)
    .pipe(gulp.dest("dist/"));
});

gulp.task("travis", function() {
  // @TODO: Configure travis tests
  return true;
});


gulp.task("build", ["smileys", "images", "sprite", "stylesheet", "vendors", "script", "merge-scripts", "copy"]);

gulp.task("default", ["build", "watch"]);
