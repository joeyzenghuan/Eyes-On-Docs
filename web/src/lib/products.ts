export const DEFAULT_PRODUCT = 'Microsoft-Foundry';

// Topic ids are stored in Cosmos DB and target_config.json. Keep ids stable,
// and use labels to make the current Foundry/classic split clear in the UI.
export const FALLBACK_PRODUCTS = [
  'Microsoft-Foundry',
  'AI-Foundry',
  'AOAI-V2',
  'Agent-Service',
  'Model-Inference',
  'AML',
  'Cog-speech-service',
  'Cog-content-understanding',
  'Cog-computer-vision',
  'Cog-content-safety',
  'Cog-custom-vision-service',
  'Cog-document-intelligence',
  'Cog-language-service',
  'Cog-translator',
  'IoT-iot-central',
  'IoT-iot-develop',
  'IoT-iot-dps',
  'IoT-iot-edge',
  'IoT-iot-hub-device-update',
  'IoT-iot-hub'
];

export const PRODUCT_LABELS: Record<string, string> = {
  'Microsoft-Foundry': 'Microsoft Foundry (new)',
  'AI-Foundry': 'AI Foundry / classic broad',
  'AOAI-V2': 'Foundry classic OpenAI',
  'Agent-Service': 'Foundry classic Agents',
  'Model-Inference': 'Model Inference (legacy)',
  AML: 'Azure Machine Learning',
  'Cog-speech-service': 'Speech service',
  'Cog-content-understanding': 'Content Understanding',
  'Cog-computer-vision': 'Computer Vision',
  'Cog-content-safety': 'Content Safety',
  'Cog-custom-vision-service': 'Custom Vision',
  'Cog-document-intelligence': 'Document Intelligence',
  'Cog-language-service': 'Language service',
  'Cog-translator': 'Translator',
  'IoT-iot-central': 'IoT Central',
  'IoT-iot-develop': 'IoT development',
  'IoT-iot-dps': 'IoT DPS',
  'IoT-iot-edge': 'IoT Edge',
  'IoT-iot-hub-device-update': 'Device Update for IoT Hub',
  'IoT-iot-hub': 'IoT Hub'
};
