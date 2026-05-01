"""
Automated dataset download script for engagement models
Downloads FER2013, COCO, and other publicly available datasets
"""

import os
import urllib.request
import zipfile
import tarfile
import gzip
import shutil
from tqdm import tqdm

class DownloadProgress:
    """Progress bar for downloads"""
    def __init__(self):
        self.pbar = None

    def __call__(self, block_num, block_size, total_size):
        if not self.pbar:
            self.pbar = tqdm(total=total_size, unit='B', unit_scale=True)
        downloaded = block_num * block_size
        if downloaded < total_size:
            self.pbar.update(block_size)
        else:
            self.pbar.close()

def download_file(url, destination):
    """Download file with progress bar"""
    print(f"Downloading {url}...")
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    urllib.request.urlretrieve(url, destination, DownloadProgress())
    print(f"Downloaded to {destination}")

def extract_archive(filepath, extract_to):
    """Extract zip/tar/gz files"""
    print(f"Extracting {filepath}...")
    os.makedirs(extract_to, exist_ok=True)
    
    if filepath.endswith('.zip'):
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif filepath.endswith('.tar.gz') or filepath.endswith('.tgz'):
        with tarfile.open(filepath, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_to)
    elif filepath.endswith('.tar'):
        with tarfile.open(filepath, 'r:') as tar_ref:
            tar_ref.extractall(extract_to)
    
    print(f"Extracted to {extract_to}")

def download_fer2013():
    """Download FER2013 dataset from Kaggle"""
    print("\n=== Downloading FER2013 Dataset ===")
    print("Note: This requires Kaggle API credentials")
    print("Setup: pip install kaggle")
    print("Place kaggle.json in ~/.kaggle/")
    
    try:
        os.system("kaggle datasets download -d msambare/fer2013 -p raw/")
        extract_archive("raw/fer2013.zip", "raw/fer2013/")
        print("FER2013 downloaded successfully!")
    except Exception as e:
        print(f"Error downloading FER2013: {e}")
        print("Please download manually from: https://www.kaggle.com/datasets/msambare/fer2013")

def download_coco_dataset():
    """Download COCO dataset for pose estimation"""
    print("\n=== Downloading COCO Dataset ===")
    
    # COCO 2017 Train images (18GB)
    coco_train_url = "http://images.cocodataset.org/zips/train2017.zip"
    coco_val_url = "http://images.cocodataset.org/zips/val2017.zip"
    coco_annotations_url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
    
    # Download validation set (smaller) for quick start
    print("Downloading COCO validation set (1GB)...")
    try:
        download_file(coco_val_url, "raw/val2017.zip")
        extract_archive("raw/val2017.zip", "raw/coco/")
        
        download_file(coco_annotations_url, "raw/annotations_trainval2017.zip")
        extract_archive("raw/annotations_trainval2017.zip", "raw/coco/")
        
        print("COCO dataset downloaded successfully!")
    except Exception as e:
        print(f"Error downloading COCO: {e}")

def download_sample_datasets():
    """Download smaller sample datasets for quick testing"""
    print("\n=== Downloading Sample Datasets ===")
    
    # Create sample directories
    os.makedirs("raw/samples/emotions", exist_ok=True)
    os.makedirs("raw/samples/poses", exist_ok=True)
    
    print("Sample datasets created. Add your own images for testing.")
    print("Structure:")
    print("  raw/samples/emotions/[happy, sad, angry, neutral, ...]")
    print("  raw/samples/poses/[sitting, standing, ...]")

def create_directory_structure():
    """Create necessary directory structure"""
    directories = [
        "raw/fer2013",
        "raw/affectnet",
        "raw/mpiigaze",
        "raw/coco",
        "raw/coco_text",
        "raw/samples",
        "processed/engagement",
        "processed/content",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # Create .gitkeep to preserve empty directories
        gitkeep_path = os.path.join(directory, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            open(gitkeep_path, 'a').close()
    
    print("Directory structure created successfully!")

def main():
    """Main download function"""
    print("=" * 60)
    print("EduSynth - Dataset Download Script")
    print("=" * 60)
    
    # Change to datasets directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create directory structure
    create_directory_structure()
    
    print("\nSelect datasets to download:")
    print("1. FER2013 (Emotion Detection) - ~300MB - Requires Kaggle API")
    print("2. COCO (Pose Estimation) - ~1GB for validation set")
    print("3. Sample datasets (for testing)")
    print("4. All publicly available datasets")
    print("5. Skip downloads (create structure only)")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == '1':
        download_fer2013()
    elif choice == '2':
        download_coco_dataset()
    elif choice == '3':
        download_sample_datasets()
    elif choice == '4':
        download_fer2013()
        download_coco_dataset()
        download_sample_datasets()
    elif choice == '5':
        print("Skipping downloads. Directory structure created.")
    else:
        print("Invalid choice. Exiting.")
    
    print("\n" + "=" * 60)
    print("Dataset setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. For AffectNet and MPIIGaze: Request access from official websites")
    print("2. Run preprocessing: cd ../ml_models && python preprocess_engagement_data.py")
    print("3. Start training: python train_engagement_model.py")
    print("\nRefer to README.md for more information on datasets.")

if __name__ == "__main__":
    main()
