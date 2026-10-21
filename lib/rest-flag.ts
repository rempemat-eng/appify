import { REST_RECOGNITION_DEFAULT } from './rest-flag-default';

/** Whether naps are credited by rest recognition (lib/rest-recognition.ts). Native reads
 *  only the default; the web build can override it from the address (lib/rest-flag.web.ts). */
export const REST_RECOGNITION: boolean = REST_RECOGNITION_DEFAULT;
