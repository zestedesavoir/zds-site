
(function () {

    function LetItSnow(element) {
        this._parent = element;

        this._canvas = document.createElement("canvas");
        var canvas = this._canvas;
        this.resize();

        canvas.style.zIndex = -1;
        canvas.style.position = "absolute";
        canvas.style.top =
            canvas.style.left =
            canvas.style.right =
            canvas.style.bottom = 0;

        canvas.style.background = window
            .getComputedStyle(this._parent)
            .getPropertyValue("background-color");
        this._parent.style.background = "transparent";

        // Append the canvas...
        if(this._parent.children.length > 0) { // As first element if there is other children
            this._parent.insertBefore(canvas, this._parent.children[0]);
        }
        else {
            this._parent.appendChild(canvas);
        }

        this._ctx = canvas.getContext("2d");

        this.setup();
    }

    LetItSnow.prototype = {
        PARTICLES_COLOR: "rgba(255, 255, 255, 0.8)", // Color
        MAX_PARTICLES: 25, // Particles limits
        SPAWN_RATE: 100, // time (ms) between two particles spawns
        PARTICLES_SPEED: 15, // Base speed
        PARTICLES_SIZE: 2, // Base size
        TURBULENCES_X: 1, // Turbulences amount (X)
        TURBULENCES_Y: 0.5, // Turbulences amount (Y)
        TURBULENCES_SPEED: 1, // Turbulences speed
        MAX_TIMESHIFT: Math.PI / 3, // Max time shifting (turbulences) between two particles

        setup: function() {
            this.particles = [];
            this._lastSpawn = this._lastLoop = Date.now();
            this.loop();

            window.addEventListener("resize", this.resize.bind(this));
        },

        resize: function() {
            var rect = this._parent.getBoundingClientRect();

            this.H = rect.height;
            this.W = rect.width;

            this._canvas.height = this.H;
            this._canvas.width = this.W;
        },

        spawnParticle: function() {
            this.particles.push({
                x: Math.random() * this.W,
                y: - this.PARTICLES_SIZE,
                d: Math.random() + 1, // Density (affects speed and size)
                s: Math.random() * this.MAX_TIMESHIFT // Time shift
            });
        },

        loop: function() {
            this.update();
            this.draw();

            requestAnimationFrame(this.loop.bind(this));
        },

        update: function() {
            var p, now = Date.now(), delta = now - this._lastLoop;
            for(var i in this.particles) {
                p = this.particles[i];
                p.y += (delta / 1000) * (this.PARTICLES_SPEED * p.d * (1.5 + Math.sin(now * this.TURBULENCES_SPEED / 1000 + p.s) * this.TURBULENCES_Y));
                p.x += (delta / 1000) * (this.PARTICLES_SPEED * p.d * (Math.cos(now * this.TURBULENCES_SPEED / 1000 + p.s) * this.TURBULENCES_X));

                if(p.y - (p.d * 4) > this.H || p.x - (p.d * 4) > this.W || p.x + (p.d * 4) < 0) {
                    this.particles.splice(i, 1);
                }
            }

            if(this._lastSpawn <= now - this.SPAWN_RATE && this.particles.length < this.MAX_PARTICLES) {
                this._lastSpawn = now;
                this.spawnParticle();
            }

            this._lastLoop = now;
        },

        draw: function() {
            this._ctx.clearRect(0, 0, this.W, this.H);

            this._ctx.fillStyle = this.PARTICLES_COLOR;
            this._ctx.beginPath();

            var p;
            for(var i in this.particles) {
                p = this.particles[i];

                this._ctx.moveTo(p.x, p.y);
                this._ctx.arc(p.x, p.y, p.d * this.PARTICLES_SIZE, 0, Math.PI*2, true);
            }

            this._ctx.fill();
        }
    };

    window.addEventListener("DOMContentLoaded", function() {
        if (document.body.className.split(" ").indexOf("vc-snow") !== -1) { // No jQuery here
            setTimeout(function() {
                window.snow = new LetItSnow(document.querySelector(".header-container > header"));
            }, 1000); // to be sure to have the DOM completely ready
        }
    });

})();
