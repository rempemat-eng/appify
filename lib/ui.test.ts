/**
 * The game menu's sheet stack (coherence plan, step 5): a sheet opened from the menu
 * returns to it; leaving for another screen closes everything; tabs are remembered.
 */
import assert from 'node:assert/strict';
import { closeAllSheets, closeSheet, openMenu, openSheet, useUi } from './ui';

openSheet('nap');
closeSheet();
assert.equal(useUi.getState().sheet, null, 'a sheet opened from the garden closes to the garden');

openMenu('bag');
assert.deepEqual([useUi.getState().sheet, useUi.getState().menuTab], ['menu', 'bag']);
openSheet('companions');
assert.equal(useUi.getState().back, 'menu', 'the companion picker remembers the menu');
closeSheet();
assert.equal(useUi.getState().sheet, 'menu', 'closing the picker returns to the menu');
assert.equal(useUi.getState().menuTab, 'bag', 'on the same tab');
closeSheet();
assert.equal(useUi.getState().sheet, null, 'closing the menu returns to the garden');

openMenu();
openSheet('rhythm');
closeAllSheets();
assert.deepEqual([useUi.getState().sheet, useUi.getState().back], [null, null]);
openMenu();
assert.equal(useUi.getState().menuTab, 'bag', 'reopening keeps the last tab');
console.log(
  'PASS: game menu sheets return to the menu, close fully when leaving and remember the tab.',
);
