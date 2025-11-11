'use strict';

/**
 * Módulo M3: Operaciones de matrices 3x3 para transformaciones 2D
 * Matrices en formato fila-mayor (row-major)
 */
export const M3 = {
  /**
   * Retorna matriz identidad
   * @returns {number[]} Matriz 3x3 identidad
   */
  identity() {
    return [
      1, 0, 0,
      0, 1, 0,
      0, 0, 1,
    ];
  },

  /**
   * Crea matriz de traslación
   * @param {number[]} t - Vector [tx, ty]
   * @returns {number[]} Matriz 3x3 de traslación
   */
  translation([tx, ty]) {
    return [
      1, 0, 0,
      0, 1, 0,
      tx, ty, 1,
    ];
  },

  /**
   * Crea matriz de rotación
   * @param {number} angleInRadians - Ángulo en radianes
   * @returns {number[]} Matriz 3x3 de rotación
   */
  rotation(angleInRadians) {
    const c = Math.cos(angleInRadians);
    const s = Math.sin(angleInRadians);
    return [
      c, s, 0,
      -s, c, 0,
      0, 0, 1,
    ];
  },

  /**
   * Crea matriz de escala
   * @param {number[]} s - Vector [sx, sy]
   * @returns {number[]} Matriz 3x3 de escala
   */
  scale([sx, sy]) {
    return [
      sx, 0, 0,
      0, sy, 0,
      0, 0, 1,
    ];
  },

  /**
   * Multiplica dos matrices 3x3
   * @param {number[]} a - Primera matriz
   * @param {number[]} b - Segunda matriz
   * @returns {number[]} Resultado de a * b
   */
  multiply(a, b) {
    const a00 = a[0], a01 = a[1], a02 = a[2];
    const a10 = a[3], a11 = a[4], a12 = a[5];
    const a20 = a[6], a21 = a[7], a22 = a[8];

    const b00 = b[0], b01 = b[1], b02 = b[2];
    const b10 = b[3], b11 = b[4], b12 = b[5];
    const b20 = b[6], b21 = b[7], b22 = b[8];

    return [
      a00 * b00 + a01 * b10 + a02 * b20,
      a00 * b01 + a01 * b11 + a02 * b21,
      a00 * b02 + a01 * b12 + a02 * b22,

      a10 * b00 + a11 * b10 + a12 * b20,
      a10 * b01 + a11 * b11 + a12 * b21,
      a10 * b02 + a11 * b12 + a12 * b22,

      a20 * b00 + a21 * b10 + a22 * b20,
      a20 * b01 + a21 * b11 + a22 * b21,
      a20 * b02 + a21 * b12 + a22 * b22,
    ];
  },
};
