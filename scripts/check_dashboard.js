// Check syntax and the control/diagnosis behavior without claiming browser visual QA.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(path.join(__dirname, '../backend/static/index.html'), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(source);
const elements = new Map();
const context = vm.createContext({
  document: {getElementById(id) {
    if (!elements.has(id)) elements.set(id, {disabled: false, textContent: '', className: ''});
    return elements.get(id);
  }},
  setTimeout,
});
vm.runInContext(source.replace(/\btick\(\);\s*$/, ''), context);
const row = {
  id:'esp32-01',connection:'online',source:'synthetic',mode:'loose',
  sensor_ok:true,clock_ready:true,sampling_ok:true,
  latest:{rms:0.2,peak:0.4,crest_factor:2,sample_count:1000,actual_hz:1000,
    window_duration_us:1000000,missed_samples:0,received_at:Date.now()/1000,
    model_ready:false,prediction:null,mode:'normal'},
};
context.row = row;
vm.runInContext("deviceRows=[row];selected=row.id;brokerConnected=true;renderDevice();", context);
assert.equal(elements.get('apply').disabled, false);
assert.equal(elements.get('prediction').textContent, 'Model unavailable');
assert.match(elements.get('modeInfo').textContent, /Loose mounting/);
for (const [key, value] of [['clock_ready',false],['sampling_ok',false],['connection','unknown'],['source','mpu6050']]) {
  const original = row[key];
  row[key] = value;
  vm.runInContext('updateControls()', context);
  assert.equal(elements.get('apply').disabled, true, key);
  row[key] = original;
}
vm.runInContext('brokerConnected=false;updateControls()', context);
assert.equal(elements.get('apply').disabled, true);
console.log('Dashboard syntax and control/diagnosis checks passed');
