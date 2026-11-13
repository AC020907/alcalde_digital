/*
 * Motor del plataformero «Ruta de la Verdad» para el navegador: traduccion 1:1 de game/clases/Plataformas.py.
 * Solo aritmetica entera y paso fijo; las constantes y el mapa llegan del servidor (config_cliente), asi que no
 * hay numeros duplicados. tests/test_plataformas_web.py ejecuta este archivo en Node con las mismas entradas que
 * el motor de Python y exige el mismo estado tick a tick. El servidor rejuega la traza que produce.
 */
(function (raiz) {
  "use strict";
  var IZQ = 1, DER = 2, SALTO = 4;
  function piso(a, b) { return Math.floor(a / b); }

  function Partida(cfg) {
    this.c = cfg.constantes;
    this.filas = cfg.filas;
    this.alto = this.filas.length;
    this.ancho = this.filas[0].length;
    this.limite = cfg.limite_ticks;
    this.evidencias = []; this.inicio = null; this.meta = null;
    for (var fy = 0; fy < this.alto; fy++) for (var fx = 0; fx < this.ancho; fx++) {
      var ch = this.filas[fy][fx];
      if (ch === "E") this.evidencias.push([fx, fy]);
      else if (ch === "S") this.inicio = [fx, fy];
      else if (ch === "M") this.meta = [fx, fy];
    }
    this.evidencias.sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
    this.tick = 0; this.estado = "jugando"; this.recogidas = []; this.muertes = 0;
    this.control = this.inicio; this.respawn = 0; this.eventos = []; this.traza = []; this.saltoPrevio = false;
    this._colocar(this.inicio);
  }
  var P = Partida.prototype;

  P.tile = function (fx, fy) {
    if (fx < 0 || fx >= this.ancho) return "#";
    if (fy < 0 || fy >= this.alto) return ".";
    return this.filas[fy][fx];
  };
  P.activo = function (tick) { return piso(tick, this.c.PARPADEO) % 2 === 0; };
  P.solido = function (fx, fy, tick) {
    var ch = this.tile(fx, fy);
    return ch === "#" || (ch === "~" && this.activo(tick));
  };
  P._colocar = function (t) {
    var c = this.c;
    this.x = t[0] * c.T + piso(c.T - c.ANCHO, 2);
    this.y = (t[1] + 1) * c.T - c.ALTO;
    this.vx = 0; this.vy = 0; this.enSuelo = false; this.coyote = 0; this.buffer = 0; this.mira = 1;
  };
  P._choca = function (x, y) {
    var c = this.c, fx0 = piso(x, c.T), fx1 = piso(x + c.ANCHO - 1, c.T), fy0 = piso(y, c.T), fy1 = piso(y + c.ALTO - 1, c.T);
    for (var fy = fy0; fy <= fy1; fy++) for (var fx = fx0; fx <= fx1; fx++) if (this.solido(fx, fy, this.tick)) return true;
    return false;
  };
  P._toca = function (fx, fy, m) {
    var c = this.c;
    return this.x < (fx + 1) * c.T - m && this.x + c.ANCHO > fx * c.T + m && this.y < (fy + 1) * c.T - m && this.y + c.ALTO > fy * c.T + m;
  };
  P.jugando = function () { return this.estado === "jugando"; };

  P.avanzar = function (mascara) {
    if (!this.jugando()) return;
    var c = this.c;
    mascara &= 7;
    var ult = this.traza[this.traza.length - 1];
    if (ult && ult[0] === mascara) ult[1] += 1; else this.traza.push([mascara, 1]);
    this.tick += 1;
    if (this.tick >= this.limite) { this.estado = "tiempo"; this.eventos.push([this.tick, "tiempo", null]); return; }
    if (this.respawn > 0) { this.respawn -= 1; this.saltoPrevio = !!(mascara & SALTO); return; }

    var dir = ((mascara & DER) ? 1 : 0) - ((mascara & IZQ) ? 1 : 0);
    if (dir) {
      this.mira = dir;
      var acel = this.enSuelo ? c.ACEL_SUELO : c.ACEL_AIRE;
      this.vx = Math.max(-c.V_MAX, Math.min(c.V_MAX, this.vx + dir * acel));
    } else if (this.vx > 0) this.vx = Math.max(0, this.vx - c.FRENO);
    else if (this.vx < 0) this.vx = Math.min(0, this.vx + c.FRENO);

    var salto = !!(mascara & SALTO);
    if (salto && !this.saltoPrevio) this.buffer = c.BUFFER; else if (this.buffer > 0) this.buffer -= 1;
    if (this.enSuelo) this.coyote = c.COYOTE; else if (this.coyote > 0) this.coyote -= 1;
    if (this.buffer > 0 && this.coyote > 0) {
      this.vy = c.V_SALTO; this.buffer = 0; this.coyote = 0; this.enSuelo = false;
      this.eventos.push([this.tick, "salto", null]);
    }
    if (!salto && this.vy < c.V_CORTE) this.vy = c.V_CORTE;
    this.saltoPrevio = salto;
    this.vy = Math.min(c.V_CAIDA_MAX, this.vy + c.GRAVEDAD);

    var nx = this.x + this.vx;
    if (this._choca(nx, this.y)) {
      if (this.vx > 0) nx = piso(nx + c.ANCHO - 1, c.T) * c.T - c.ANCHO;
      else if (this.vx < 0) nx = (piso(nx, c.T) + 1) * c.T;
      else nx = this.x;
      if (this._choca(nx, this.y)) nx = this.x;
      this.vx = 0;
    }
    this.x = nx;
    var ny = this.y + this.vy, estabaEnSuelo = this.enSuelo;
    this.enSuelo = false;
    if (this.vy < 0 && this._choca(this.x, ny)) {          // correccion de esquina (igual que Plataformas.py)
      for (var dx = 16; dx <= c.ESQUINA; dx += 16) {
        if (!this._choca(this.x + dx, ny) && !this._choca(this.x + dx, this.y)) { this.x += dx; break; }
        if (!this._choca(this.x - dx, ny) && !this._choca(this.x - dx, this.y)) { this.x -= dx; break; }
      }
    }
    if (this._choca(this.x, ny)) {
      if (this.vy > 0) { ny = piso(ny + c.ALTO - 1, c.T) * c.T - c.ALTO; this.enSuelo = true; }
      else if (this.vy < 0) ny = (piso(ny, c.T) + 1) * c.T;
      else ny = this.y;
      if (this._choca(this.x, ny)) ny = this.y;
      if (this.enSuelo && !estabaEnSuelo) this.eventos.push([this.tick, "aterriza", null]);
      this.vy = 0;
    }
    this.y = ny;

    if (this.y > this.alto * c.T || this._choca(this.x, this.y)) return this._morir();
    var fx0 = piso(this.x, c.T), fx1 = piso(this.x + c.ANCHO - 1, c.T), fy0 = piso(this.y, c.T), fy1 = piso(this.y + c.ALTO - 1, c.T);
    for (var fy = fy0; fy <= fy1; fy++) for (var fx = fx0; fx <= fx1; fx++) {
      var ch = this.tile(fx, fy);
      if (ch === "^" && this._toca(fx, fy, c.MARGEN_PINCHO)) return this._morir();
      if (ch === "E") {
        var i = -1;
        for (var k = 0; k < this.evidencias.length; k++) if (this.evidencias[k][0] === fx && this.evidencias[k][1] === fy) i = k;
        if (this.recogidas.indexOf(i) < 0) { this.recogidas.push(i); this.eventos.push([this.tick, "evidencia", i]); }
      } else if (ch === "C" && !(fx === this.control[0] && fy === this.control[1]) && fx > this.control[0]) {
        this.control = [fx, fy]; this.eventos.push([this.tick, "control", null]);
      } else if (ch === "M") { this.estado = "meta"; this.eventos.push([this.tick, "meta", null]); return; }
    }
  };
  P._morir = function () {
    this.muertes += 1; this.respawn = this.c.RESPAWN_TICKS;
    this.eventos.push([this.tick, "dano", null]);
    this._colocar(this.control);
  };
  P.abandonar = function () { if (this.jugando()) this.estado = "abandono"; };
  P.completado = function () { return this.estado === "meta"; };
  P.puntuacion = function () {
    var total = this.evidencias.length;
    var p = total ? piso(550 * this.recogidas.length + piso(total, 2), total) : 0;
    if (this.completado()) {
      var resto = Math.max(0, this.limite - this.tick);
      p += 250 + piso(150 * resto, this.limite) + Math.max(0, 50 - 10 * this.muertes);
    }
    return p;
  };
  P.huella = function () { return [this.tick, this.x, this.y, this.vx, this.vy, this.muertes, this.recogidas.length, this.estado]; };

  var api = { Partida: Partida, IZQ: IZQ, DER: DER, SALTO: SALTO };
  if (typeof module === "object" && module.exports) module.exports = api; else raiz.PlatCivitas = api;
})(this);
