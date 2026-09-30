/** Automated runs never open an AudioContext, including URL overrides. Offline rendering is silent. */
export function silentAutomation(): boolean {
  return typeof navigator !== 'undefined' && navigator.webdriver === true;
}
