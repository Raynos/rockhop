/** Standalone browser bundle injected only by the headless hero capture harness. */
export { prepareSurfaceContacts, CONTACT_IDS } from './surface-contacts.mjs';
/** Identity probe: the private bundle must share the live game's Three constructors. */
export { Vector3 as ContactVector3 } from 'three';
