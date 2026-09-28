# Shastra Proof Yard

## Overview

Shastra Proof Yard is a professional desktop application designed for analyzing ballistic proof test results using computer vision technology. The application processes before-and-after images of shooting targets to automatically detect shot impacts, calculate statistical metrics, and generate comprehensive PDF reports for quality assurance and compliance documentation.

### Application Workflow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main Page     │    │  Preview Page   │    │ Settings Page   │    │   Report        │
│                 │    │                 │    │                 │    │   Generation    │
│ • Upload Images │    │ • Review Results│    │ • Configure     │    │                 │
│ • Enter Metadata│    │ • Edit Shots    │    │ • Generate      │    │ • PDF Creation  │
│ • Process       │    │ • Adjust Zoom   │    │   Markers       │    │ • Save Results  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         └───────────────────────┼───────────────────────┼───────────────────────┘
                                 │                       │
                    ┌────────────┴────────────┐          │
                    │    Session Manager      │          │
                    │ • State Management      │          │
                    │ • File I/O              │          │
                    │ • Data Persistence      │          │
                    └────────────┬────────────┘          │
                                 │                       │
                    ┌────────────┴───────────┐     ┌─────┴─────┐
                    │     Vision Core        │     │  Config   │
                    │ • Image Processing     │     │ • Settings│
                    │ • Statistical Analysis │     │ • Storage │
                    └────────────────────────┘     └───────────┘
```

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Features](#features)
- [Architecture](#architecture)
- [User Interface](#user-interface)
- [Configuration](#configuration)
- [Image Processing Pipeline](#image-processing-pipeline)
- [Report Generation](#report-generation)
- [Update System](#update-system)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

## System Requirements

### Operating Systems
- Windows 7 or later
- Linux (Ubuntu 18.04+, Debian, Fedora)
- macOS 10.14+

### Hardware Requirements
- Processor: 2.0 GHz dual-core or better
- RAM: 4 GB minimum, 8 GB recommended
- Storage: 500 MB for application, additional space for image database and reports
- Display: 1280x720 minimum resolution, 1920x1080 recommended

### Software Dependencies
- Python 3.7 or later
- PyQt5 5.15.0+
- OpenCV 4.5.0+
- NumPy 1.21.0+
- ReportLab 3.6.0+
- Pillow 8.0.0+
- Requests 2.25.0+
- Packaging 21.0+
- Keyring 23.0.0+

## Installation

### Method 1: From Source

1. Clone or download the repository
2. Navigate to the project directory
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the application:
```bash
python main.py
```

### Method 2: Standalone Executable

Download the platform-specific executable from the releases page and run directly. No Python installation required.

## Features

### Core Functionality

#### 1. Image Analysis and Shot Detection
- **Automatic Shot Detection**: Uses computer vision algorithms to automatically identify bullet holes in target images
- **ArUco Marker-Based Alignment**: Employs ArUco markers (ID 0-3) for precise image alignment and perspective correction
- **Manual Shot Addition**: Allows users to manually mark missed shot impacts by clicking on the preview image
- **Shot Deletion**: Enables removal of false positives detected by the automatic system
- **Real-time Recalculation**: Statistics update instantly when shots are added or removed

#### 2. Statistical Analysis
The application calculates and displays comprehensive ballistic metrics:

- **Shot Count**: Total number of detected impacts
- **Mean Point of Impact (MPI)**: Average position of all shots in millimeters
- **Mean Radius Deviation (MRD)**: Average distance of shots from the MPI
- **Max Horizontal Spread**: Maximum horizontal distance between any two shots
- **Max Vertical Spread**: Maximum vertical distance between any two shots
- **Individual Shot Deviations**: Distance from MPI for each individual shot
- **Pass/Fail Status**: Automatic determination based on configurable deviation threshold

#### 3. Session Management
- **New Session Creation**: Start fresh analysis sessions with clear state management
- **Session Data Persistence**: Saves all session data including images and analysis results
- **Session History**: Organizes results by timestamp in structured directories
- **Form Data Storage**: Captures and stores metadata for each test session

#### 4. Report Generation
- **PDF Export**: Generates professional PDF reports with A4 page layout
- **Custom Branding**: Includes organization logos and headers
- **Metadata Tables**: Documents test conditions, weapon details, lot numbers
- **Visual Results**: Embeds annotated target images showing shot positions
- **Statistical Summary**: Presents all calculated metrics in tabular format
- **Approval Section**: Includes signature line for authorized personnel

#### 5. Interactive Preview Interface
- **Image Zoom Controls**: Zoom in/out with adjustable scale factor (0.5x to 5.0x)
- **Fit to Window**: Automatically scales image to fit available space
- **Click-to-Add Shots**: Left-click to manually add shot markers
- **Click-to-Delete Shots**: Right-click on existing markers to remove them
- **Visual Differentiation**: Automatic shots in red, manual shots in cyan
- **Scrollable Canvas**: Navigate large images with smooth scrolling
- **Real-time Annotation**: Immediate visual feedback for all modifications

### Configuration System

#### System Configuration Panel
- **Marker Grid Size**: Configure the physical dimensions of the target area (width x height in mm)
- **ArUco Marker Size**: Set the physical size of ArUco markers used for alignment (mm)
- **Sheet Size**: Define the overall target sheet dimensions (mm)
- **Output Resolution**: Set the pixel dimensions for processed images (width x height)
- **File Path Management**: 
  - Input image folder selection
  - Output report folder configuration
  - Image database location
  - Generated markers storage location
- **Format Selection**:
  - Image format (PNG, JPEG, BMP)
  - Report format (PDF)

#### Advanced Settings Panel
Fine-tune the computer vision algorithms:

- **Difference Threshold**: Controls sensitivity to pixel value changes (0-255)
- **Median Blur Kernel**: Noise reduction filter size (odd numbers: 3, 5, 7, etc.)
- **Morphology Kernel Size**: Blob refinement kernel dimensions (width x height)
- **Dilation Iterations**: Number of morphological dilation passes
- **Min Hole Area**: Minimum pixel area to consider as valid shot (excludes noise)
- **Max Hole Area**: Maximum pixel area to consider as valid shot (excludes large defects)
- **Distance Transform Threshold**: Watershed algorithm separation sensitivity (0.0-1.0)
- **Max Mean Deviation**: Pass/fail threshold in millimeters

#### Configuration Persistence
- Settings stored in platform-specific locations:
  - Windows: Registry (HKEY_CURRENT_USER\Software\Shastra_Proof_Yard)
  - Linux: ~/.config/Shastra_Proof_Yard/config_settings.conf
  - macOS: ~/Library/Preferences/com.Shastra_Proof_Yard.config_settings.plist
- Restore to Factory Defaults: Single-click restoration of all default values
- Automatic Configuration Loading: Settings persist across application sessions

### ArUco Marker Generation
- **Built-in Generator**: Creates ArUco markers directly from the application
- **PDF Output**: Generates printable PDF files for each marker (IDs 0-3)
- **DICT_6X6_250 Dictionary**: Uses standard 6x6 ArUco marker format
- **Precise Sizing**: Markers sized according to configured physical dimensions
- **Padded Borders**: Includes white padding for improved detection reliability
- **Dotted Frame**: Visual guides for accurate marker placement
- **Batch Generation**: Creates all four required markers in one operation

### Update System
- **Automatic Update Checking**: Checks for new versions on application startup
- **GitHub Integration**: Connects to private GitHub repository for enterprise deployments
- **Secure Authentication**: Uses token-based authentication for private repositories
- **Local Network Support**: Can update from local file servers for offline environments
- **Platform-Specific Builds**: Detects and downloads appropriate executables (Windows/Linux/macOS)
- **Version Verification**: SHA-256 hash checking for download integrity
- **Seamless Updates**: Downloads, verifies, and applies updates with automatic restart
- **Update Confirmation**: Displays notification when update completes successfully
- **Version Display**: Shows current version number in the UI

### User Interface Features

#### Responsive Design
- **Adaptive Layouts**: Automatically adjusts to different screen sizes and resolutions
- **Breakpoint-Based Rendering**: 
  - Small screens (< 600px): Single column, stacked buttons
  - Medium screens (600-900px): Single column, inline buttons
  - Large screens (> 900px): Two-column layout with side-by-side cards
- **Scrollable Content**: All pages support vertical scrolling for smaller displays
- **Resizable Panels**: Splitter control for adjusting preview/control panel ratio
- **Maximized Launch**: Application starts maximized for optimal workspace usage

#### Theme and Styling
- **Modern Material Design**: Clean, professional appearance with card-based layouts
- **Consistent Color Scheme**: Primary blue (#1976D2) with complementary accents
- **Custom Scrollbars**: Styled vertical and horizontal scrollbars with hover effects
- **Button States**: Visual feedback for hover and pressed states
- **Rounded Corners**: Smooth 6-14px border radius for modern aesthetic
- **Shadows and Borders**: Subtle elevation effects for depth perception

#### Navigation
- **Three-Page Structure**:
  1. Main Page: Image upload and form entry
  2. Preview Page: Analysis results and interactive editing
  3. Settings Page: Configuration management
- **Back Navigation**: Easy return to previous screens
- **Menu Bar**: Quick access to key functions
- **Keyboard Shortcuts**: Support for standard keyboard navigation

## Architecture

### Design Pattern
The application follows the Model-View-Controller (MVC) architecture:

- **Model**: `VisionCore` handles all computer vision algorithms and calculations
- **View**: PyQt5 widgets and pages manage user interface presentation
- **Controller**: `SessionManager` coordinates data flow between model and view

### MVC Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (View)                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Main Page     │  │  Preview Page   │  │Settings Page│  │
│  │ • Form Fields   │  │ • Image Display │  │ • Config UI │  │
│  │ • Upload Areas  │  │ • Controls      │  │ • Advanced  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ User Actions
                      │ (Signals/Slots)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Controller (SessionManager)                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │Session State    │  │File Operations  │  │Data Flow    │  │
│  │• Image Paths    │  │• Load/Save      │  │• Validation │  │
│  │• Shot Data      │  │• Export         │  │• Processing │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Processing Requests
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Model (VisionCore)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │Image Alignment  │  │Shot Detection   │  │Statistics   │  │
│  │• ArUco Markers  │  │• Difference     │  │• MPI/MRD    │  │
│  │• Homography     │  │• Filtering      │  │• Pass/Fail  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Structure

#### Architecture Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Shastra Proof Yard                         │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Frontend Layer (View)                        ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ ││
│  │  │ main_window │  │ main_page  │  │preview_page│  │settings_  │ ││
│  │  │     .py     │  │    .py     │  │    .py     │  │  page.py  │ ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ ││
│  └─────────────────────────────────────────────────────────────────┘│
│                    │                                                │
│                    │ PyQt5 Signals/Slots                            │
│                    ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                   Controller (SessionManager)                   ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ ││
│  │  │Session State│  │File I/O     │  │Data Flow    │  │Validation│││
│  │  │Management   │  │Operations   │  │Coordination │  │& Logic   │││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ ││
│  └─────────────────────────────────────────────────────────────────┘│
│                    │                                                │
│                    │ Processing Requests                            │
│                    ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Model (VisionCore)                           ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ ││
│  │  │Image Align- │  │Shot Detect- │  │Statistical  │  │Config   │ ││
│  │  │ment & Warp  │  │ion Pipeline │  │Analysis     │  │Interface│ ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Components & Utilities                       ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │|
│  │  │UI Components│  │Workers &   │  │Report Gen  │  │Update    │  ││
│  │  │(upload_btn, │  │Validators  │  │& ArUco     │  │System    │  ││
│  │  │form_fields) │  │(async ops) │  │Markers     │  │         │   ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Configuration & Storage                      ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ ││
│  │  │System Config│  │File Paths  │   │Image DB     │  │Session  │ ││
│  │  │(QSettings)  │  │Management  │   │Storage      │  │Data     │ ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

#### Backend Layer
- **config.py**: System configuration management with persistent storage
- **vision_core.py**: Core computer vision processing engine
- **session_manager.py**: Session state management and file I/O operations

#### Frontend Layer
- **main_window.py**: Primary application window and page orchestration
- **main_page.py**: Initial form and image upload interface
- **preview_page.py**: Interactive results display and editing
- **settings_page.py**: Configuration panel interface

#### Components Package
Reusable UI components:
- **upload_button.py**: Drag-and-drop file upload widget
- **form_fields.py**: Standardized input field components
- **preview_controls.py**: Statistics display and control panel
- **advanced_settings.py**: Vision algorithm parameter controls
- **system_configs.py**: System-level configuration interface
- **menu_helpers.py**: Menu bar construction utilities
- **styled_input.py**: Custom-styled input widgets
- **ui_shared.py**: Shared UI components (loading overlay, interactive labels)

#### Utilities Package
Helper functions and workers:
- **aruco_markers.py**: ArUco marker PDF generation
- **report_generator.py**: PDF report creation engine
- **generate_result.py**: Result data processing
- **workers.py**: Background thread workers for async operations
- **validators.py**: Input validation functions
- **formatter.py**: Data formatting utilities
- **resource_path.py**: Resource file path resolution for bundled executables
- **error_message.py**: Error handling and display

#### Update System Package
- **update_checker.py**: Version checking and download management
- **update_dialog.py**: Update notification UI
- **updater.py**: Update application and main app replacement

## User Interface

### Main Page

#### Header Section
- **Application Title**: Centered title with flanking organization logos
- **New Session Button**: Clears current session and resets all fields
- **Settings Button**: Opens configuration panel

#### Upload Section
Two upload areas for image input:
1. **Before Image Upload**:
   - Drag-and-drop or click to browse
   - Shows preview thumbnail after selection
   - Displays filename below thumbnail
   - Validates ArUco marker presence

2. **After Image Upload**:
   - Identical interface to Before upload
   - Accepts same image formats
   - Independent validation

#### Form Fields
Structured data entry for test documentation:
- **AMK Number**: Asset management identifier
- **Nomenclature**: Test item description
- **Lot Number**: Manufacturing lot identifier
- **Weapon Used**: Firearm specification
- **Sample Size**: Number of rounds fired
- **Range Temperature**: Environmental conditions

#### Action Buttons
- **Generate Result**: Initiates analysis pipeline
  - Validates all inputs
  - Transitions to Preview Page
  - Starts background processing

### Preview Page

#### Top Bar
- **Back Button**: Returns to Main Page without saving
- **Page Title**: Context indicator

#### Split Panel Layout

##### Left Panel: Image Display
- **Canvas Area**: Shows processed target image with annotations
- **Shot Markers**:
  - Red circles: Automatically detected shots
  - Cyan circles: Manually added shots
  - Numbered labels: Shot identification
- **Zoom Controls**: Accessible via right panel
- **Interaction Modes**:
  - Left-click empty area: Add manual shot
  - Right-click shot marker: Delete shot

##### Right Panel: Control Panel
Divided into three sections:

1. **Zoom Controls**:
   - Zoom In button (1.25x increment)
   - Zoom Out button (0.8x decrement)
   - Zoom level slider (0.5x to 5.0x)
   - Fit to Window button (auto-scale)

2. **Statistics Display**:
   - Shot count with visual counter
   - Mean Point of Impact coordinates
   - Mean Radius Deviation with color-coded threshold
   - Max horizontal spread
   - Max vertical spread
   - Pass/Fail indicator with color coding (green/red)

3. **Action Buttons**:
   - **Save Results**: Generates and saves PDF report
     - Shows loading overlay during generation
     - Displays success message with file location
     - Opens file location in system file manager

### Settings Page

#### Header Bar
- **Back Button**: Returns to Main Page
- **Page Title**: "Settings"
- **Generate Markers Button**: Creates ArUco marker PDFs
- **Restore Defaults Button**: Resets all settings to factory defaults

#### Configuration Cards
Two-column responsive layout:

##### Left Column: System Configuration
- Marker grid dimensions input
- ArUco marker size input
- Sheet size dimensions
- Output resolution settings
- File path selectors with browse buttons
- Format dropdown menus

##### Right Column: Advanced Settings
- All vision algorithm parameters
- Numeric input fields with validation
- Real-time parameter updating
- Descriptive labels and units

## Configuration

### Physical Setup Configuration

#### Marker Grid Size
Defines the physical area between ArUco markers:
- **Default**: 800mm x 800mm
- **Purpose**: Establishes the coordinate system for measurements
- **Recommendation**: Measure actual distance between marker centers

#### ArUco Marker Size
Physical dimensions of each marker:
- **Default**: 100mm x 100mm
- **Purpose**: Used for masking corners during difference calculation
- **Recommendation**: Match the size of printed markers

#### Sheet Size
Overall dimensions of the target sheet:
- **Default**: 914.4mm x 914.4mm (36 inches)
- **Purpose**: Documentation and report generation
- **Recommendation**: Use actual target sheet dimensions

### Image Processing Configuration

#### Output Resolution
Pixel dimensions for warped/aligned images:
- **Default**: 1000px x 1000px
- **Purpose**: Defines processing resolution and affects mm-to-pixel conversion
- **Trade-off**: Higher resolution = better accuracy but slower processing

#### Difference Threshold
Pixel intensity difference to consider as shot:
- **Default**: 90 (0-255 scale)
- **Lower values**: More sensitive, may detect noise
- **Higher values**: Less sensitive, may miss faint holes
- **Recommendation**: 70-110 for most scenarios

#### Median Blur Kernel
Pre-processing noise reduction:
- **Default**: 5
- **Must be odd number**: 3, 5, 7, 9, etc.
- **Larger values**: More aggressive noise removal but may blur shot edges
- **Recommendation**: 3-7 for most scenarios

#### Morphology Kernel Size
Shape refinement operations:
- **Default**: 5x5 pixels
- **Purpose**: Removes small noise artifacts and smooths shot boundaries
- **Larger values**: More aggressive cleanup
- **Recommendation**: 3x3 to 7x7

#### Dilation Iterations
Blob expansion passes:
- **Default**: 1
- **Purpose**: Connects nearby pixels and fills small gaps
- **More iterations**: Larger detected areas
- **Recommendation**: 1-3 iterations

#### Min/Max Hole Area
Valid shot size range in pixels:
- **Min Default**: 50 pixels
- **Max Default**: 50000 pixels
- **Purpose**: Filters out noise (too small) and large defects (too large)
- **Recommendation**: Adjust based on caliber and range distance

#### Distance Transform Threshold
Watershed algorithm separation parameter:
- **Default**: 0.5 (0.0-1.0 scale)
- **Lower values**: More aggressive separation of touching blobs
- **Higher values**: More conservative, may not separate close shots
- **Recommendation**: 0.3-0.7 for most scenarios

#### Max Mean Deviation
Pass/fail criterion:
- **Default**: 14.0 mm
- **Purpose**: Maximum acceptable Mean Radius Deviation
- **Usage**: Tests pass if MRD ≤ this value
- **Recommendation**: Set according to acceptance criteria

## Image Processing Pipeline

### Pipeline Overview Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Input     │    │   Stage 1   │    │   Stage 2   │    │   Stage 3   │
│   Images    │───▶│   Loading   │───▶│   ArUco     │───▶│ Difference  │
│             │    │  & Validate │    │  Alignment  │    │ Calculation │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                          │
                                                          ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Stage 4   │    │   Stage 5   │    │   Stage 6   │    │   Stage 7   │
│   Noise     │───▶│   Blob      │───▶│   Contour   │───▶│ Statistical │
│   Filtering │    │   Separation│    │   Extraction│    │   Analysis  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Stage 8: Output                      │
│              ┌─────────────────┐  ┌─────────────────┐   │
│              │   Annotated     │  │   Analysis      │   │
│              │   Image         │  │   Results       │   │
│              └─────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Detailed Pipeline Flow

```
Input Images
    │
    ├── Reference Image (Before Shooting)
    └── Shot Image (After Shooting)
    │
    ▼ Stage 1: Image Loading & Validation
    │
    ├── Load images from file paths
    ├── Validate successful decoding
    └── Check reasonable dimensions
    │
    ▼ Stage 2: ArUco Marker Detection & Alignment
    │
    ├── Convert to grayscale
    ├── Detect ArUco markers (IDs 0-3)
    ├── Extract marker centers
    ├── Verify all markers present
    ├── Calculate homography matrix
    ├── Apply perspective transformation
    └── Output: Aligned images at OUTPUT_PX resolution
    │
    ▼ Stage 3: Difference Calculation
    │
    ├── Convert aligned images to grayscale
    ├── Calculate absolute pixel difference: |I_after - I_before|
    ├── Mask corner regions (ArUco markers)
    └── Output: Difference image highlighting changes
    │
    ▼ Stage 4: Noise Filtering
    │
    ├── Apply median blur (kernel size)
    ├── Binary thresholding (threshold value)
    ├── Morphological opening (kernel size)
    ├── Dilation (iterations)
    └── Output: Clean binary image with shot candidates
    │
    ▼ Stage 5: Blob Separation (Watershed)
    │
    ├── Calculate distance transform
    ├── Identify sure foreground/background
    ├── Apply connected components labeling
    ├── Execute watershed algorithm
    ├── Remove watershed boundaries
    └── Output: Separated shot candidates
    │
    ▼ Stage 6: Contour Extraction
    │
    ├── Find external contours
    ├── Filter by area (min/max hole area)
    ├── Calculate centroids using image moments
    ├── Convert pixel → millimeter coordinates
    └── Output: List of shot candidates (id, x_mm, y_mm, area)
    │
    ▼ Stage 7: Statistical Analysis
    │
    ├── Extract coordinates of active shots
    ├── Calculate Mean Point of Impact (MPI)
    ├── Calculate distances from MPI
    ├── Calculate Mean Radius Deviation (MRD)
    ├── Calculate max spreads (horizontal/vertical)
    ├── Apply pass/fail criterion
    └── Output: AnalysisResult object
    │
    ▼ Stage 8: Visualization & Annotation
        │
        ├── Copy shot warped image
        ├── Draw circles at shot positions
        ├── Color-code (red=auto, cyan=manual)
        ├── Add numeric labels
        └── Output: Annotated image for display/reporting
```

## Report Generation

### Report Structure Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        A4 PDF Page                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Header Section                   │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ Left Logo   │  │   Title     │  │ Right Logo  │  │    │
│  │  │  (15mm)     │  │ SHASTRA     │  │  (15mm)     │  │    │
│  │  │             │  │ PROOF YARD  │  │             │  │    │
│  │  │             │  │ Proof Test  │  │             │  │    │
│  │  │             │  │ Results     │  │             │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Metadata Table                      │    │
│  │  ┌─────────────────────────────────────────────────┐│    │
│  │  │ Date and Time Conducted     │ [Value]           ││    │
│  │  ├─────────────────────────────────────────────────┤│    │
│  │  │ AMK No                       │ [Value]          ││    │
│  │  ├─────────────────────────────────────────────────┤│    │
│  │  │ Nomenclature                 │ [Value]          ││    │
│  │  ├─────────────────────────────────────────────────┤│    │
│  │  │ Lot No                       │ [Value]          ││    │
│  │  ├─────────────────────────────────────────────────┤│    │
│  │  │ Weapon used for firing       │ [Value]          ││    │
│  │  ├─────────────────────────────────────────────────┤│    │
│  │  │ Sample Size                  │ [Value]          ││    │
│  │  ├─────────────────────────────────────────────────┤│    │
│  │  │ Range Temperature            │ [Value]          ││    │
│  │  └─────────────────────────────────────────────────┘│    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Target Image                        │    │
│  │                                                     │    │
│  │              [Annotated Shot Image]                 │    │
│  │              (140mm x 140mm)                        │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Results Summary                        │    │
│  │                                                     │    │
│  │  MPI = (X.XX, Y.YY) mm    Deviation = Z.ZZ mm       │    │
│  │                                                     │    │
│  │                    [PASS/FAIL]                      │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Results Table                       │    │
│  │  ┌─────────────────────────────────────────────────┐│    │
│  │  │ Round No. │ Distance from MPI │ Muzzle Velocity ││    │
│  │  │           │ (mm)              │ (m/s)           ││    │
│  │  ├─────────────────────────────────────────────────┤│    │
│  │  │ 1         │ XX.XX             │ XXX.XX          ││    │
│  │  ├─────────────────────────────────────────────────┤│    │
│  │  │ 2         │ XX.XX             │ XXX.XX          ││    │
│  │  ├─────────────────────────────────────────────────┤│    │
│  │  │ ...       │ ...               │ ...             ││    │
│  │  └─────────────────────────────────────────────────┘│    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Approval Section                       │    │
│  │                                                     │    │
│  │                    Approved By                      │    │
│  │                    ___________                      │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Report File Management

#### File Organization
```
results/
  Session_YYYYMMDD_HHMMSS/
    raw_shot.jpg          # Unmodified aligned image
    annotated_shot.jpg    # Image with shot markers
    report.pdf            # Generated report
```

#### Filename Convention
- **Session Directory**: Session_[timestamp]
  - Timestamp format: YYYYMMDD_HHMMSS
  - Example: Session_20231215_143022
- **Report Filename**: report.pdf
- **Raw Image**: raw_shot.jpg
- **Annotated Image**: annotated_shot.jpg

#### Save Location
Configurable through settings:
- Default: `<application_directory>/results/`
- Custom: User-selectable via Settings page
- Automatic directory creation if not exists

## Update System

### Update Process Flow Diagram

```
┌─────────────────┐
│   App Startup   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│  Check Version  │────▶│  Compare with   │
│   (Local)       │     │   Remote        │
└─────────────────┘     └─────────┬───────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Version       │
                        │   Comparison    │
                        └─────────┬───────┘
                                  │
                                  ▼
┌─────────────────┐             ┌─────────────────┐
│   Up to Date    │◀────────────│   Newer         │
│   Continue      │             │   Version       │
└─────────────────┘             │   Available     │
                                └─────────┬───────┘
                                          │
                                          ▼
                                ┌─────────────────┐
                                │   Show Update   │
                                │   Dialog        │
                                └─────────┬───────┘
                                          │
                                          ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Update Now    │  │ Update on Exit  │  │     Skip        │
│                 │  │                 │  │                 │
└─────────┬───────┘  └─────────┬───────┘  └─────────────────┘
          │                    │
          └─────────┬──────────┘
                    │
                    ▼
          ┌─────────────────┐
          │   Download      │
          │   New Version   │
          └─────────┬───────┘
                    │
                    ▼
          ┌─────────────────┐
          │   Verify Hash   │
          └─────────┬───────┘
                    │
                    ▼
          ┌─────────────────┐
          │   Launch        │
          │   Updater       │
          └─────────┬───────┘
                    │
                    ▼
          ┌─────────────────┐
          │   Wait for      │
          │   Main App      │
          │   to Exit       │
          └─────────┬───────┘
                    │
                    ▼
          ┌─────────────────┐
          │   Replace       │
          │   Executable    │
          └─────────┬───────┘
                    │
                    ▼
          ┌─────────────────┐
          │   Launch New    │
          │   Version       │
          └─────────┬───────┘
                    │
                    ▼
          ┌─────────────────┐
          │   Show Update   │
          │   Complete      │
          │   Notification  │
          └─────────────────┘
```

### Update Configuration

#### GitHub Authentication
For private repositories:
- Set token via Settings dialog
- Token stored in OS keyring (secure)
- Required permissions: Read access to releases
- Generate at: GitHub Settings > Developer Settings > Personal Access Tokens

#### Version File Format (version_linux.json example)
```json
{
  "version": "1.1.0",
  "download_url": "https://api.github.com/repos/owner/repo/releases/assets/12345",
  "release_notes": "New features:\n- Feature 1\n- Feature 2",
  "sha256": "abc123...",
  "size_bytes": 52428800,
  "min_version": "1.0.0"
}
```

#### Platform Detection
Automatic detection of:
- Operating system (Windows, Linux, macOS)
- Architecture (32-bit, 64-bit)
- Executable naming conventions
- File permissions and execution requirements

## Usage Guide

### First-Time Setup

#### 1. Install Application
- Download and install from source or use standalone executable
- Launch application
- Application creates default configuration

#### 2. Configure Physical Setup
Navigate to Settings page:
- Set Marker Grid Size to match your target setup
- Set ArUco Marker Size to match printed markers
- Set Sheet Size if different from default

#### 3. Generate ArUco Markers
- Click "Generate Markers" button in Settings
- Select output folder
- Print the generated PDFs (marker_id_0.pdf through marker_id_3.pdf)
- Affix markers to target frame:
  - ID 0: Top-Left
  - ID 1: Top-Right
  - ID 2: Bottom-Left
  - ID 3: Bottom-Right

#### 4. Configure File Paths
In Settings page:
- Set input image folder (where you store target photos)
- Set output report folder (where PDFs will be saved)
- Set image database folder (where analysis data is stored)

### Normal Operation Workflow

#### Workflow Overview Diagram

```
┌─────────────────┐
│   Prepare       │
│   Images        │
│ • Before/After  │
│ • ArUco Markers │
│ • Good Lighting │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Start New     │
│   Session       │
│ • Clear State   │
│ • Upload Images │
│ • Enter Metadata│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Generate      │
│   Analysis      │
│ • Auto Detection│
│ • Computer Vision│
│ • Statistical Calc│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐     ┌─────────────────┐
│   Review &      │────▶│   Manual        │
│   Edit Results  │     │   Adjustments   │
│ • Check Shots   │     │ • Add Missing   │
│ • Verify Stats  │     │ • Delete False  │
│ • Zoom/Pan      │     │ • Real-time     │
└─────────────────┘     └─────────────────┘
          │
          ▼
┌─────────────────┐
│   Save Results  │
│ • Generate PDF  │
│ • Export Images │
│ • Session Data  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Continue or   │
│   Exit          │
│ • New Session   │
│ • Close App     │
└─────────────────┘
```

#### Step 1: Prepare Images
1. Photograph clean target (before shooting)
   - Ensure all four ArUco markers visible
   - Good lighting, minimal shadows
   - Camera perpendicular to target
   - Sufficient resolution (2MP minimum)

2. Conduct shooting test

3. Photograph target with shots (after shooting)
   - Same camera position and angle
   - Same lighting conditions
   - All markers still visible

#### Step 2: Start Session
1. Click "New Session" if previous session active
2. Upload before image:
   - Drag and drop onto upload area, or
   - Click upload button and browse to file
3. Upload after image using same method
4. Verify both thumbnails display correctly

#### Step 3: Enter Metadata
Fill in form fields:
- AMK Number (asset identifier)
- Nomenclature (test item name)
- Lot Number (manufacturing lot)
- Weapon Used (firearm specification)
- Sample Size (number of rounds)
- Temperature (environmental conditions)

#### Step 4: Generate Analysis
1. Click "Generate Result" button
2. Wait for processing (5-30 seconds typical)
3. Automatic transition to Preview Page

#### Step 5: Review and Edit Results
On Preview Page:
- Review automatically detected shots (red circles)
- Check statistics panel for metrics
- If shots missed:
  - Left-click empty area to add manual shot
  - Shot appears in cyan
- If false positives detected:
  - Right-click shot marker to delete
- Statistics update in real-time after each change

#### Step 6: Adjust View
Use zoom controls as needed:
- Click "Zoom In" / "Zoom Out" buttons
- Use zoom slider for precise control
- Click "Fit to Window" to reset
- Scroll canvas to navigate zoomed image

#### Step 7: Save Results
1. Click "Save Results" button
2. Wait for PDF generation (2-5 seconds)
3. Success dialog shows:
   - Save location
   - Option to open folder
4. Click "Open Folder" to view results

#### Step 8: Continue or Exit
- Click "Back" to start new session
- Close application to exit

### Advanced Usage

#### Tuning Detection Parameters
If automatic detection fails or produces false positives:

1. Navigate to Settings > Advanced Settings
2. Adjust parameters iteratively:
   
   For missing shots (false negatives):
   - Decrease Difference Threshold (try -10 at a time)
   - Decrease Min Hole Area (but not below 20)
   - Increase Median Blur Kernel cautiously
   
   For false positives:
   - Increase Difference Threshold (try +10 at a time)
   - Increase Min Hole Area
   - Decrease Distance Transform Threshold
   
3. Return to Main Page and reprocess images
4. Repeat until optimal detection achieved
5. Settings persist for future sessions

#### Batch Processing Workflow
For multiple tests:

1. Organize images in folders by session
2. For each session:
   - New Session
   - Upload images
   - Enter metadata (copy/paste common fields)
   - Generate Result
   - Quick review
   - Save Results
3. All reports saved in organized session folders

#### Custom Pass/Fail Criteria
To change acceptance threshold:
1. Settings > Advanced Settings
2. Set "Max Mean Deviation" to desired value in mm
3. All future analyses use new threshold
4. Pass/Fail indicator updates accordingly

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Alignment Failed: ArUco markers not found"
Causes:
- Markers not visible in image
- Markers damaged or obscured
- Image quality too low
- Wrong marker dictionary

Solutions:
- Ensure all four markers visible in both images
- Re-print markers if damaged
- Use higher resolution camera
- Verify markers generated with this application

#### Issue: Shots not detected automatically
Causes:
- Low contrast between hole and target
- Difference threshold too high
- Min hole area too large
- Lighting inconsistent between images

Solutions:
- Adjust Difference Threshold lower (try 70-80)
- Reduce Min Hole Area to 30-40
- Retake images with consistent lighting
- Use manual shot addition as workaround

#### Issue: False positives detected
Causes:
- Target debris or damage
- Lighting changes between images
- Difference threshold too low
- Max hole area too large

Solutions:
- Clean target between reference and shot images
- Increase Difference Threshold (try 100-110)
- Reduce Max Hole Area
- Delete false positives manually

#### Issue: Incorrect measurements
Causes:
- Wrong Marker Grid Size setting
- Wrong ArUco Marker Size
- Markers not placed accurately
- Image distortion

Solutions:
- Measure actual marker spacing, update in Settings
- Verify marker size matches configuration
- Re-position markers with precise measurement
- Ensure camera perpendicular to target

#### Issue: Application won't start
Causes:
- Missing dependencies
- Corrupted configuration
- Insufficient permissions
- Python version mismatch

Solutions:
- Reinstall dependencies: `pip install -r requirements.txt`
- Delete configuration file and restart
- Run as administrator (Windows) or with sudo (Linux)
- Verify Python 3.7+ installed

#### Issue: PDF generation fails
Causes:
- No write permission to output folder
- Disk space full
- Invalid characters in metadata
- Missing font files

Solutions:
- Check folder permissions
- Free up disk space
- Avoid special characters in form fields
- Reinstall ReportLab: `pip install --force-reinstall reportlab`

#### Issue: Update fails
Causes:
- No internet connection
- Invalid GitHub token
- Firewall blocking download
- Insufficient disk space

Solutions:
- Check network connectivity
- Verify GitHub token has correct permissions
- Configure firewall to allow application
- Free up space in temp folder

## Technical Details

### Computer Vision Algorithms

#### ArUco Marker Detection
- **Library**: OpenCV ArUco module
- **Dictionary**: DICT_6X6_250 (250 unique 6x6 bit markers)
- **Detection**: Sub-pixel corner refinement
- **Marker IDs**: 0 (TL), 1 (TR), 2 (BL), 3 (BR)

#### Homography Transformation
- **Method**: cv2.findHomography with RANSAC
- **Purpose**: Corrects perspective distortion
- **Output**: Aligned images in orthogonal view
- **Accuracy**: Sub-pixel precision

#### Difference Calculation
- **Method**: Absolute difference of grayscale images
- **Formula**: |I_after(x,y) - I_before(x,y)|
- **Corner Masking**: Excludes marker regions (1.2x marker size)

#### Noise Filtering
- **Median Blur**: Non-linear edge-preserving filter
- **Binary Threshold**: Converts to black/white
- **Morphological Opening**: Removes small noise
- **Dilation**: Connects fragmented regions

#### Watershed Segmentation
- **Purpose**: Separates touching/overlapping shots
- **Distance Transform**: Identifies blob centers
- **Marker-Based Watershed**: Controlled region growing
- **Boundary Detection**: Identifies separation lines

#### Contour Analysis
- **Method**: cv2.findContours with RETR_EXTERNAL
- **Approximation**: CHAIN_APPROX_SIMPLE
- **Centroid Calculation**: Image moments (M10/M00, M01/M00)
- **Area Filtering**: Excludes contours outside size range

### Statistical Formulas

#### Mean Point of Impact (MPI)
```
MPI_x = (1/n) * Σ(x_i) for i=1 to n
MPI_y = (1/n) * Σ(y_i) for i=1 to n
```

#### Mean Radius Deviation (MRD)
```
d_i = √((x_i - MPI_x)² + (y_i - MPI_y)²)
MRD = (1/n) * Σ(d_i) for i=1 to n
```

#### Horizontal Spread
```
H_spread = max(x_i) - min(x_i)
```

#### Vertical Spread
```
V_spread = max(y_i) - min(y_i)
```

#### Pass/Fail Criterion
```
Pass if: MRD ≤ MAX_MEAN_DEVIATION_MM
Fail if: MRD > MAX_MEAN_DEVIATION_MM
```

### Coordinate Systems

#### Pixel Coordinates
- Origin: Top-left corner
- X-axis: Left to right (0 to OUTPUT_PX[0])
- Y-axis: Top to bottom (0 to OUTPUT_PX[1])
- Units: Pixels

#### Millimeter Coordinates
- Origin: Top-left marker position
- X-axis: Left to right (0 to MARKER_GRID_SIZE_MM[0])
- Y-axis: Top to bottom (0 to MARKER_GRID_SIZE_MM[1])
- Units: Millimeters
- Conversion: mm = px * (MARKER_GRID_SIZE_MM / OUTPUT_PX)

### File Formats

#### Supported Input Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)

#### Output Formats
- Report: PDF (A4 size, 210x297mm)
- Images: JPEG (default), PNG, BMP
- Markers: PDF with embedded image

### Threading and Async Operations

#### Background Workers
- **SessionWorker**: Runs image processing pipeline
- **ReportWorker**: Generates PDF reports
- **UpdateWorker**: Downloads and verifies updates

#### Thread Safety
- All Qt widgets accessed from main GUI thread only
- Workers communicate via Qt signals
- Progress updates through signal/slot mechanism

#### Loading Indicators
- Loading overlay with animation during processing
- Progress bars for downloads
- Disabled buttons during operations

### Performance Considerations

#### Memory Usage
- Typical: 200-500 MB
- Peak: 1-2 GB for very large images
- Image caching: One before, one after, one result

#### Processing Time
- Alignment: 0.5-2 seconds
- Detection: 2-10 seconds
- Statistics: < 0.1 seconds
- Total: 5-30 seconds typical

#### Optimization Tips
- Use OUTPUT_PX around 1000-2000 for balance
- Avoid excessively large input images (> 20MP)
- Close unused sessions to free memory
- Regular cleanup of image database folder

### Security Considerations

#### Token Storage
- GitHub tokens stored in OS keyring
- Windows: Credential Manager
- Linux: GNOME Keyring, KWallet
- macOS: Keychain
- Never stored in plain text

#### Update Verification
- SHA-256 hash verification mandatory
- Rejects downloads with hash mismatch
- Prevents malicious file replacement
- Secure HTTPS connections for downloads

#### File Permissions
- Creates files with user-only write permission
- Respects OS security policies
- No elevation required for normal operation

## License

Proprietary software. All rights reserved.

## Support

For technical support, bug reports, or feature requests, please contact the development team.

## Version History

### Version 1.0.0
- Initial release
- Automatic shot detection with ArUco alignment
- Interactive preview with manual editing
- PDF report generation
- Comprehensive statistics calculation
- Settings persistence
- ArUco marker generation
- GitHub update system
- Responsive UI design
