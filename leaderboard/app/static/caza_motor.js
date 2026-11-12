/*
 * Motor de Caza-Rumores para el navegador: traduccion 1:1 de game/clases/arena/caza_web.py (clase Caza).
 * Paso fijo de 50 ms y solo enteros. El escenario (cuentas, conexiones, focos, tiempos) llega del servidor.
 * tests/test_caza_web.py compara este archivo (Node) con el motor de Python tick a tick.
 */
(function (raiz) {
  "use strict";
  function Caza(cfg) {
    this.cfg = cfg; this.TICK = cfg.tick_ms;
    this.pos = {}; this.salidas = {};
    var i;
    for (i = 0; i < cfg.nodos.length; i++) this.pos[cfg.nodos[i].id] = [cfg.nodos[i].x, cfg.nodos[i].y];
    for (i = 0; i < cfg.aristas.length; i++) {
      var a = cfg.aristas[i];
      (this.salidas[a[0]] = this.salidas[a[0]] || []).push([a[1], a[2]]);
    }
    this.tick = 0; this.totalTicks = Math.floor(cfg.duracion_ms / this.TICK);
    this.contagiados = {}; this.orden = []; this.proximo = {}; this.paquetes = []; this.interceptados = 0; this.eventos = [];
    for (i = 0; i < cfg.focos.length; i++) this._contagiar(cfg.focos[i], 0);
  }
  var C = Caza.prototype;
  C._contagiar = function (nodo, t) {
    if (nodo in this.contagiados) return;
    this.contagiados[nodo] = t; this.orden.push(nodo); this.eventos.push([t, "contagio", nodo]);
    var s = this.salidas[nodo] || [];
    for (var k = 0; k < s.length; k++) this.proximo[nodo + ">" + s[k][0]] = t + this.cfg.retardo_ms + k * this.cfg.escalon_ms;
  };
  C.terminado = function () { return this.tick >= this.totalTicks; };
  C.enVuelo = function (pid) { return pid >= 0 && pid < this.paquetes.length && this.paquetes[pid].estado === "vuelo"; };
  C.posicion = function (pid, t) {
    var p = this.paquetes[pid], a = this.pos[p.a], b = this.pos[p.b], dur = p.llega - p.sale;
    var k = Math.max(0, Math.min(dur, t - p.sale));
    return [a[0] + Math.floor((b[0] - a[0]) * k / dur), a[1] + Math.floor((b[1] - a[1]) * k / dur)];
  };
  C.interceptar = function (pid) {
    if (!this.enVuelo(pid)) return false;
    this.paquetes[pid].estado = "interceptado"; this.interceptados += 1;
    this.eventos.push([this.tick * this.TICK, "intercepcion", pid]);
    return true;
  };
  C.avanzar = function () {
    if (this.terminado()) return;
    this.tick += 1;
    var t = this.tick * this.TICK, i, p;
    for (i = 0; i < this.paquetes.length; i++) {
      p = this.paquetes[i];
      if (p.estado === "vuelo" && p.llega <= t) { p.estado = "llego"; this._contagiar(p.b, t); }
    }
    var activos = {};
    for (i = 0; i < this.paquetes.length; i++) if (this.paquetes[i].estado === "vuelo") activos[this.paquetes[i].a + ">" + this.paquetes[i].b] = true;
    var orden = this.orden.slice();
    for (i = 0; i < orden.length; i++) {
      var a = orden[i], s = this.salidas[a] || [];
      for (var k = 0; k < s.length; k++) {
        var b = s[k][0], dur = s[k][1], clave = a + ">" + b;
        if (b in this.contagiados || activos[clave] || this.proximo[clave] > t) continue;
        this.paquetes.push({ id: this.paquetes.length, a: a, b: b, sale: t, llega: t + dur, estado: "vuelo" });
        this.proximo[clave] = t + dur + this.cfg.reemision_ms;
        activos[clave] = true;
      }
    }
  };
  C.nContagiados = function () { return this.orden.length; };
  C.huella = function () {
    var v = 0;
    for (var i = 0; i < this.paquetes.length; i++) if (this.paquetes[i].estado === "vuelo") v++;
    return [this.tick, this.orden.length, this.paquetes.length, this.interceptados, v];
  };
  /* Paquete en vuelo mas cercano a (x, y) dentro del radio, o -1. */
  C.buscar = function (x, y, radio) {
    var mejor = -1, d2 = radio * radio, t = this.tick * this.TICK;
    for (var i = 0; i < this.paquetes.length; i++) {
      if (this.paquetes[i].estado !== "vuelo") continue;
      var q = this.posicion(i, t), d = (q[0] - x) * (q[0] - x) + (q[1] - y) * (q[1] - y);
      if (d <= d2) { d2 = d; mejor = i; }
    }
    return mejor;
  };

  var api = { Caza: Caza };
  if (typeof module === "object" && module.exports) module.exports = api; else raiz.CazaCivitas = api;
})(this);
