import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

// Hard-coded fallback product list
const FALLBACK_PRODUCTS = [
  'AI-Foundry',
  'AOAI-V2',
  'Agent-Service',
  'Model-Inference',
  'AML',
  'Cog-speech-service',
  'Cog-document-intelligence',
  'Cog-language-service',
  'Cog-translator',
  'Cog-content-safety',
  'Cog-computer-vision',
  'Cog-custom-vision-service',
  'IoT-iot-hub',
  'IoT-iot-edge',
  'IoT-iot-dps',
  'IoT-iot-central',
  'IoT-iot-hub-device-update'
];

interface TargetConfig {
  topic_name: string;
  language?: string;
  [key: string]: any;
}

export async function GET() {
  try {
    // Path to target_config.json in the root directory
    const configPath = path.join(process.cwd(), '..', 'target_config.json');
    
    // Check if file exists
    if (!fs.existsSync(configPath)) {
      console.error(`Config file not found at: ${configPath}, using fallback products`);
      return NextResponse.json({ 
        products: FALLBACK_PRODUCTS,
        source: 'fallback',
        error: 'Config file not found'
      });
    }

    // Read and parse the config file
    const fileContent = fs.readFileSync(configPath, 'utf-8');
    const config: TargetConfig[] = JSON.parse(fileContent);

    // Extract unique topic names while preserving order
    const seenTopics = new Set<string>();
    const products: string[] = [];

    for (const item of config) {
      if (item.topic_name && !seenTopics.has(item.topic_name)) {
        seenTopics.add(item.topic_name);
        products.push(item.topic_name);
      }
    }

    // If no products found, use fallback
    if (products.length === 0) {
      console.error('No topic_name found in config file, using fallback products');
      return NextResponse.json({ 
        products: FALLBACK_PRODUCTS,
        source: 'fallback',
        error: 'No topics found in config'
      });
    }

    return NextResponse.json({ 
      products,
      source: 'config',
      count: products.length
    });

  } catch (error) {
    console.error('Error reading target_config.json:', error);
    return NextResponse.json({ 
      products: FALLBACK_PRODUCTS,
      source: 'fallback',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
