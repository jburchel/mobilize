/**
 * Image Optimization Script for Mobilize CRM
 * This script optimizes images and generates WebP versions
 */

const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

// Define source and destination directories
const sourceDir = path.join(__dirname, '../app/static/images');
const destDir = path.join(__dirname, '../app/static/images/optimized');

// Create destination directory if it doesn't exist
if (!fs.existsSync(destDir)) {
  fs.mkdirSync(destDir, { recursive: true });
  console.log(`Created directory: ${destDir}`);
}

// Process images function
async function processImages() {
  try {
    // Read all files in the source directory
    const files = fs.readdirSync(sourceDir);
    
    // Filter out non-image files and directories
    const imageFiles = files.filter(file => {
      const filePath = path.join(sourceDir, file);
      const isDirectory = fs.statSync(filePath).isDirectory();
      const extension = path.extname(file).toLowerCase();
      const isImage = ['.jpg', '.jpeg', '.png', '.gif', '.svg'].includes(extension);
      
      return !isDirectory && isImage;
    });
    
    console.log(`Found ${imageFiles.length} images to process`);
    
    // Process each image
    for (const file of imageFiles) {
      const sourceFilePath = path.join(sourceDir, file);
      const fileBaseName = path.basename(file, path.extname(file));
      const fileExt = path.extname(file).toLowerCase();
      
      // Skip already processed files
      if (fileBaseName.endsWith('-optimized')) {
        continue;
      }
      
      console.log(`Processing: ${file}`);
      
      // Process based on file type
      if (['.jpg', '.jpeg', '.png'].includes(fileExt)) {
        // Create optimized version
        const optimizedFilePath = path.join(destDir, `${fileBaseName}-optimized${fileExt}`);
        await sharp(sourceFilePath)
          .resize({
            width: 1200,
            height: 1200,
            fit: 'inside',
            withoutEnlargement: true
          })
          .toFile(optimizedFilePath);
        
        // Create WebP version
        const webpFilePath = path.join(destDir, `${fileBaseName}.webp`);
        await sharp(sourceFilePath)
          .resize({
            width: 1200,
            height: 1200,
            fit: 'inside',
            withoutEnlargement: true
          })
          .webp({ quality: 80 })
          .toFile(webpFilePath);
        
        // Create responsive sizes for WebP
        const sizes = [300, 600, 900];
        for (const size of sizes) {
          const responsiveWebpFilePath = path.join(destDir, `${fileBaseName}-${size}.webp`);
          await sharp(sourceFilePath)
            .resize({
              width: size,
              height: size,
              fit: 'inside',
              withoutEnlargement: true
            })
            .webp({ quality: 80 })
            .toFile(responsiveWebpFilePath);
        }
      } else if (fileExt === '.svg') {
        // Just copy SVG files
        const destFilePath = path.join(destDir, file);
        fs.copyFileSync(sourceFilePath, destFilePath);
      }
    }
    
    console.log('Image optimization complete!');
  } catch (error) {
    console.error('Error processing images:', error);
  }
}

// Run the image processing
processImages(); 