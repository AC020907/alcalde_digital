/*
 * Motor del Duelo de Frecuencias para el navegador: traduccion 1:1 de game/clases/Ritmo.py (clase Duelo).
 * No tiene numeros propios: ventanas y valores llegan del servidor (GET /api/arena/ritmo/<modo>), que los lee
 * de Ritmo.py. tests/test_ritmo_web.py ejecuta este archivo en Node y comprueba que juzga EXACTAMENTE igual
 * que el motor de Python con las mismas pulsaciones (a 30, 60 y 144 Hz, con jitter).
 *
 * Tambien incluye la estimacion del reloj del servidor (SyncReloj) para el inicio coordinado.
 */
(function (raiz) {
  "use strict";

  function MotorDuelo(chart, ventanas, valores, rompen) {
    this.chart = chart;
    this.v = ventanas;
    this.valores = valores;
    this.rompen = rompen || ["bad", "miss"];
    this.notas = chart.notes.map(function (n) { return { time_ms: n.time_ms, lane: n.lane, estado: null, desvio: null }; });
    this.siguiente = 0;
    this.conteo = { perfect: 0, good: 0, bad: 0, miss: 0 };
    this.combo = 0;
    this.maxCombo = 0;
    this.estado = "countdown";
    this.ultimos = [];
  }

  MotorDuelo.prototype.empezar = function () { if (this.estado === "countdown") this.estado = "playing"; };

  MotorDuelo.prototype.actualizar = function (t) {
    if (this.estado !== "playing") return;
    var limite = t - this.v.bad, i = this.siguiente;
    while (i < this.notas.length && this.notas[i].time_ms < limite) {
      if (this.notas[i].estado === null) this._juzgar(i, "miss", t, null);
      i++;
    }
    this.siguiente = i;
    if (t >= this.chart.duration_ms && this.notas.every(function (n) { return n.estado; })) this.estado = "results";
  };

  MotorDuelo.prototype.pulsar = function (carril, t) {
    if (this.estado !== "playing") return null;
    var mejor = -1;
    for (var i = this.siguiente; i < this.notas.length; i++) {
      var n = this.notas[i];
      if (n.time_ms - t > this.v.bad) break;
      if (n.estado === null && n.lane === carril && Math.abs(n.time_ms - t) <= this.v.bad) { mejor = i; break; }
    }
    if (mejor < 0) return null;
    var d = Math.abs(this.notas[mejor].time_ms - t);
    var juicio = d <= this.v.perfect ? "perfect" : d <= this.v.good ? "good" : "bad";
    this._juzgar(mejor, juicio, t, Math.round(t - this.notas[mejor].time_ms));
    return juicio;
  };

  MotorDuelo.prototype._juzgar = function (i, juicio, t, desvio) {
    this.notas[i].estado = juicio;
    this.notas[i].desvio = desvio;
    this.conteo[juicio] += 1;
    if (this.rompen.indexOf(juicio) < 0) { this.combo += 1; this.maxCombo = Math.max(this.maxCombo, this.combo); }
    else this.combo = 0;
    this.ultimos = this.ultimos.concat([[t, this.notas[i].lane, juicio]]).slice(-8);
  };

  /* Termina la cancion (abandono, pestaña cerrada...): lo no juzgado cuenta como Miss. */
  MotorDuelo.prototype.cerrar = function (t) {
    for (var i = 0; i < this.notas.length; i++) if (this.notas[i].estado === null) this._juzgar(i, "miss", t, null);
    this.estado = "results";
  };

  MotorDuelo.prototype.juzgadas = function () { return this.conteo.perfect + this.conteo.good + this.conteo.bad + this.conteo.miss; };

  MotorDuelo.prototype.suma = function () {
    var s = 0, c = this.conteo, v = this.valores;
    for (var k in c) s += v[k] * c[k];
    return s;
  };

  MotorDuelo.prototype.precision = function () { return this.notas.length ? this.suma() / this.notas.length : 0; };

  /* Precision de lo jugado hasta ahora (barra señal/interferencia). */
  MotorDuelo.prototype.senal = function () { var j = this.juzgadas(); return j ? this.suma() / j : 0.5; };

  /* Misma formula que torneo.puntuar_ritmo: al terminar coincide con lo que calcula el servidor. */
  MotorDuelo.prototype.puntos = function () {
    var n = this.notas.length;
    return n ? Math.round(850 * this.suma() / n + 150 * this.maxCombo / n) : 0;
  };

  MotorDuelo.prototype.resultado = function () {
    return {
      dificultad: "normal",
      juicios: this.notas.map(function (n) { return n.estado || "miss"; }),
      desvios: this.notas.map(function (n) { return n.estado && n.estado !== "miss" ? n.desvio : null; })
    };
  };

  /*
   * Reloj del servidor: cada respuesta trae "faltan X ms" para el inicio. Con la hora local de envio y de
   * recepcion se estima el instante local de inicio = recibido - RTT/2 + faltan. Se usa la muestra de menor
   * RTT (la menos afectada por colas de red); un salto grande de la estimacion sin RTT mejor se ignora.
   */
  function SyncReloj() { this.muestras = []; this.inicioLocal = null; this.rtt = null; }

  SyncReloj.prototype.agregar = function (enviado, recibido, faltanMs) {
    var rtt = Math.max(0, recibido - enviado);
    var estimado = recibido - rtt / 2 + faltanMs;
    this.muestras.push({ rtt: rtt, est: estimado });
    if (this.muestras.length > 30) this.muestras.shift();
    var mejores = this.muestras.slice().sort(function (a, b) { return a.rtt - b.rtt; }).slice(0, 3);
    var ests = mejores.map(function (m) { return m.est; }).sort(function (a, b) { return a - b; });
    this.inicioLocal = ests[Math.floor(ests.length / 2)];
    this.rtt = mejores[0].rtt;
    return this.inicioLocal;
  };

  var api = { MotorDuelo: MotorDuelo, SyncReloj: SyncReloj };
  if (typeof module === "object" && module.exports) module.exports = api;
  else raiz.RitmoCivitas = api;
})(this);
