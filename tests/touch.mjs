import assert from 'node:assert/strict';
import {normaliseStick,installTouchControls} from '../mobile_controls.js';
const v=normaliseStick(100,-100);assert.ok(Math.abs(Math.hypot(v.right,v.forward)-1)<.001);assert.ok(v.forward>0&&v.right>0);
assert.equal(normaliseStick(0,0).forward,0);
class Target{constructor(){this.listeners={};this.style={};}addEventListener(n,f){(this.listeners[n]??=[]).push(f)}setPointerCapture(){}getBoundingClientRect(){return {left:0,top:0,width:120,height:120}}emit(n,e){for(const f of this.listeners[n]||[])f({preventDefault(){},pointerType:'touch',...e})}}
const canvas=new Target(),pad=new Target(),knob=new Target();let look=[0,0];globalThis.document=new Target();globalThis.addEventListener=()=>{};
const input=installTouchControls({canvas,pad,knob,onLook:(x,y)=>{look=[x,y]}});
pad.emit('pointerdown',{pointerId:1,clientX:60,clientY:20});assert.ok(input.forward>.9);
canvas.emit('pointerdown',{pointerId:2,clientX:100,clientY:100});canvas.emit('pointermove',{pointerId:2,clientX:130,clientY:110});assert.deepEqual(look,[.12,.04]);assert.ok(input.forward>.9);
pad.emit('pointercancel',{pointerId:1});assert.equal(input.forward,0);assert.equal(input.right,0);
canvas.emit('pointerup',{pointerId:2});canvas.emit('pointermove',{pointerId:2,clientX:180,clientY:120});assert.deepEqual(look,[.12,.04]);
pad.emit('pointerdown',{pointerId:3,clientX:100,clientY:60});assert.ok(input.right>.9);document.hidden=true;document.emit('visibilitychange',{});assert.equal(input.right,0);
console.log('PASS: joystick limits, simultaneous movement/look, touch cancellation and background reset.');
