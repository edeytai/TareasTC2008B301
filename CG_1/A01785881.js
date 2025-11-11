/*
 * Script to draw a 2D face with transformations and pivot rotation
 *
 * Emiliano Deyta
 * 2025-11-11
 */

'use strict';

// Use global twgl from CDN
import { M3 } from './transforms2d.js';

// Define the shader code, using GLSL 3.00

const vsGLSL = `#version 300 es
in vec2 a_position;

uniform vec2 u_resolution;
uniform mat3 u_transforms;

void main() {
    // Apply transformations
    vec2 position = (u_transforms * vec3(a_position, 1.0)).xy;

    // Convert the position from pixels to 0.0 - 1.0
    vec2 zeroToOne = position / u_resolution;

    // Convert from 0->1 to 0->2
    vec2 zeroToTwo = zeroToOne * 2.0;

    // Convert from 0->2 to -1->1 (clip space)
    vec2 clipSpace = zeroToTwo - 1.0;

    // Invert Y axis
    gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
}
`;

const fsGLSL = `#version 300 es
precision highp float;

uniform vec4 u_color;

out vec4 outColor;

void main() {
    outColor = u_color;
}
`;

// Parameters for the UI
const params = {
    tx: 600,
    ty: 400,
    angleDeg: 0,
    sx: 1.0,
    sy: 1.0,
    px: 600,
    py: 400,
};

// Generate a regular polygon (disc)
function createPolygon(cx, cy, radius, sides) {
    const positions = [];

    // Center of the polygon
    positions.push(cx, cy);

    // Perimeter vertices
    for (let i = 0; i <= sides; i++) {
        const angle = (i / sides) * Math.PI * 2;
        const x = cx + Math.cos(angle) * radius;
        const y = cy + Math.sin(angle) * radius;
        positions.push(x, y);
    }

    return positions;
}

// Generate a triangle
function createTriangle(x1, y1, x2, y2, x3, y3) {
    return [x1, y1, x2, y2, x3, y3];
}

// Generate face geometry (yellow polygon + black eyes and mouth)
function createFaceGeometry() {
    const positions = [];

    // Base face (16-sided polygon)
    const face = createPolygon(0, 0, 80, 16);
    positions.push(...face);

    // Left eye (triangle)
    const leftEye = createTriangle(-30, -20, -20, -30, -10, -20);
    positions.push(...leftEye);

    // Right eye (triangle)
    const rightEye = createTriangle(10, -20, 20, -30, 30, -20);
    positions.push(...rightEye);

    // Mouth (curved with multiple small triangles)
    const mouthSegments = 8;
    const mouthRadius = 50;
    const mouthStartAngle = Math.PI * 0.2;
    const mouthEndAngle = Math.PI * 0.8;

    for (let i = 0; i < mouthSegments; i++) {
        const angle1 = mouthStartAngle + (i / mouthSegments) * (mouthEndAngle - mouthStartAngle);
        const angle2 = mouthStartAngle + ((i + 1) / mouthSegments) * (mouthEndAngle - mouthStartAngle);

        const x1 = Math.cos(angle1) * mouthRadius;
        const y1 = Math.sin(angle1) * mouthRadius + 10;
        const x2 = Math.cos(angle2) * mouthRadius;
        const y2 = Math.sin(angle2) * mouthRadius + 10;

        const mouth = createTriangle(0, 30, x1, y1, x2, y2);
        positions.push(...mouth);
    }

    return {
        a_position: { numComponents: 2, data: positions },
    };
}

// Generate pivot geometry (diamond shape)
function createPivotGeometry() {
    const size = 10;

    return {
        a_position: {
            numComponents: 2,
            data: [
                0, -size,    // top
                -size, 0,    // left
                0, size,     // bottom
                size, 0,     // right
            ],
        },
    };
}

// Convert degrees to radians
function degToRad(degrees) {
    return degrees * Math.PI / 180;
}

function main() {
    const canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl2');

    const programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);

    // Create geometries
    const faceArrays = createFaceGeometry();
    const pivotArrays = createPivotGeometry();

    // Create buffer info
    const faceBufferInfo = twgl.createBufferInfoFromArrays(gl, faceArrays);
    const pivotBufferInfo = twgl.createBufferInfoFromArrays(gl, pivotArrays);

    // Create VAOs
    const faceVAO = twgl.createVAOFromBufferInfo(gl, programInfo, faceBufferInfo);
    const pivotVAO = twgl.createVAOFromBufferInfo(gl, programInfo, pivotBufferInfo);

    // Setup GUI
    const gui = new lil.GUI({ title: 'Controls' });

    const modelFolder = gui.addFolder('Model');
    modelFolder.add(params, 'tx', 0, 1200, 1).name('Translation X');
    modelFolder.add(params, 'ty', 0, 800, 1).name('Translation Y');
    modelFolder.add(params, 'angleDeg', -180, 180, 0.1).name('Rotation (deg)');
    modelFolder.add(params, 'sx', 0.1, 5, 0.01).name('Scale X');
    modelFolder.add(params, 'sy', 0.1, 5, 0.01).name('Scale Y');
    modelFolder.open();

    const pivotFolder = gui.addFolder('Pivot');
    pivotFolder.add(params, 'px', 0, 1200, 1).name('Translation X');
    pivotFolder.add(params, 'py', 0, 800, 1).name('Translation Y');
    pivotFolder.open();

    // Reset button
    gui.add({
        reset: () => {
            params.tx = 600;
            params.ty = 400;
            params.angleDeg = 0;
            params.sx = 1.0;
            params.sy = 1.0;
            params.px = 600;
            params.py = 400;
            gui.controllersRecursive().forEach(c => c.updateDisplay());
        }
    }, 'reset').name('Reset');

    // Start rendering
    drawScene(gl, programInfo, faceVAO, faceBufferInfo, pivotVAO, pivotBufferInfo);
}

// Function to do the actual display of the objects
function drawScene(gl, programInfo, faceVAO, faceBufferInfo, pivotVAO, pivotBufferInfo) {
    twgl.resizeCanvasToDisplaySize(gl.canvas);

    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    gl.clearColor(0.9, 0.9, 0.9, 1);
    gl.clear(gl.COLOR_BUFFER_BIT);

    gl.useProgram(programInfo.program);

    // Calculate pivot matrix (translation only)
    const pivotMatrix = M3.translation([params.px, params.py]);

    // Calculate face matrix: M = T × S × Tp × R × Tnp
    const T = M3.translation([params.tx, params.ty]);
    const S = M3.scale([params.sx, params.sy]);
    const R = M3.rotation(degToRad(params.angleDeg));
    const Tp = M3.translation([params.px, params.py]);
    const Tnp = M3.translation([-params.px, -params.py]);

    // Compose transformations: T * S * Tp * R * Tnp
    let faceMatrix = M3.multiply(Tnp, M3.identity());
    faceMatrix = M3.multiply(R, faceMatrix);
    faceMatrix = M3.multiply(Tp, faceMatrix);
    faceMatrix = M3.multiply(S, faceMatrix);
    faceMatrix = M3.multiply(T, faceMatrix);

    // Common uniforms
    const commonUniforms = {
        u_resolution: [gl.canvas.width, gl.canvas.height],
    };

    // Draw pivot first (behind)
    gl.bindVertexArray(pivotVAO);
    twgl.setUniforms(programInfo, {
        ...commonUniforms,
        u_transforms: pivotMatrix,
        u_color: [0.5, 0.5, 0.5, 1],
    });
    twgl.drawBufferInfo(gl, pivotBufferInfo, gl.TRIANGLE_FAN);

    // Draw face on top
    gl.bindVertexArray(faceVAO);

    // Draw base polygon (yellow)
    twgl.setUniforms(programInfo, {
        ...commonUniforms,
        u_transforms: faceMatrix,
        u_color: [1, 1, 0, 1],
    });
    gl.drawArrays(gl.TRIANGLE_FAN, 0, 18); // 1 center + 17 vertices

    // Draw eyes and mouth (black)
    twgl.setUniforms(programInfo, {
        u_color: [0, 0, 0, 1],
    });
    gl.drawArrays(gl.TRIANGLES, 18, 3 + 3 + 8 * 3); // 2 eyes + 8 mouth triangles

    requestAnimationFrame(() => drawScene(gl, programInfo, faceVAO, faceBufferInfo, pivotVAO, pivotBufferInfo));
}

main();
