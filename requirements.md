# Requirements Document

## Introduction

ระบบเปรียบเทียบไฟล์ Excel อัตโนมัติสำหรับการจัดการข้อมูล IT Asset เป็นระบบที่ออกแบบมาเพื่อเปรียบเทียบข้อมูล IT Asset จากไฟล์หลัก (Master File) ที่มาจากระบบ ERP กับไฟล์ข้อมูล Inventory 3 ประเภท (Hardware, Software, และ UPS/Monitor) เพื่อค้นหาความไม่ตรงกันและสร้างรายงานสำหรับการแก้ไขข้อมูล

ระบบจะมี Dashboard แสดงเปอร์เซ็นต์ความตรงกัน สามารถอัพโหลดไฟล์เพื่อเปรียบเทียบ สร้างรายงาน Excel ที่แสดงความไม่ตรงกัน รองรับการแก้ไขข้อมูลและเปรียบเทียบซ้ำได้

## Glossary

- **System**: ระบบเปรียบเทียบไฟล์ Excel อัตโนมัติทั้งหมด
- **Master_File**: ไฟล์ Excel หลักจากระบบ ERP (0-FTI_asset_HWSWOth.xlsx) ที่เก็บข้อมูล IT Asset ทั้งหมด
- **Inventory_File**: ไฟล์ Excel ข้อมูล Inventory ที่ต้องการเปรียบเทียบกับ Master_File (Hardware, Software, UPS/Monitor)
- **Mismatch_Report**: รายงานไฟล์ Excel ที่แสดงรายการข้อมูลที่ไม่ตรงกันระหว่าง Master_File และ Inventory_File
- **Dashboard**: หน้าจอแสดงสรุปผลการเปรียบเทียบแบบ Web-based
- **Comparison_Engine**: โมดูลที่ทำหน้าที่เปรียบเทียบข้อมูลระหว่างไฟล์
- **File_Uploader**: โมดูลที่จัดการการอัพโหลดไฟล์ Excel
- **Report_Generator**: โมดูลที่สร้างไฟล์รายงาน Excel
- **Data_Corrector**: โมดูลที่จัดการการแก้ไขข้อมูลและเปรียบเทียบซ้ำ
- **Match_Percentage**: เปอร์เซ็นต์ความตรงกันระหว่างข้อมูลใน Master_File และ Inventory_File
- **Asset_ID**: รหัสประจำตัวของ Asset ที่ใช้เป็น Primary Key ในการเปรียบเทียบ
- **User**: ผู้ใช้งานระบบที่ต้องการเปรียบเทียบและจัดการข้อมูล IT Asset

## Requirements

### Requirement 1: File Upload and Management

**User Story:** As a User, I want to upload Excel files to the system, so that I can compare Master_File with Inventory_File

#### Acceptance Criteria

1. THE File_Uploader SHALL accept Excel files in .xlsx format
2. WHEN a User uploads a file, THE File_Uploader SHALL validate that the file is not corrupted
3. WHEN a User uploads a file, THE File_Uploader SHALL validate that the file contains required columns
4. THE File_Uploader SHALL support uploading one Master_File and multiple Inventory_File (up to 3 files)
5. IF a file fails validation, THEN THE File_Uploader SHALL display a descriptive error message to the User
6. WHEN a file is successfully uploaded, THE File_Uploader SHALL display the filename and file size to the User

### Requirement 2: Data Comparison

**User Story:** As a User, I want the system to compare Master_File with Inventory_File automatically, so that I can identify data mismatches

#### Acceptance Criteria

1. WHEN a User initiates comparison, THE Comparison_Engine SHALL read data from Master_File and all uploaded Inventory_File
2. THE Comparison_Engine SHALL match records between Master_File and Inventory_File using Asset_ID as the primary key
3. WHEN comparing Hardware inventory, THE Comparison_Engine SHALL compare Asset_ID, Model, Serial_Number, Location, and Status fields
4. WHEN comparing Software inventory, THE Comparison_Engine SHALL compare Asset_ID, Software_Name, License_Key, Version, and Installation_Date fields
5. WHEN comparing UPS/Monitor inventory, THE Comparison_Engine SHALL compare Asset_ID, Device_Type, Model, Serial_Number, and Location fields
6. THE Comparison_Engine SHALL identify records that exist in Master_File but not in Inventory_File
7. THE Comparison_Engine SHALL identify records that exist in Inventory_File but not in Master_File
8. THE Comparison_Engine SHALL identify records where field values do not match between files
9. WHEN comparison is complete, THE Comparison_Engine SHALL calculate Match_Percentage for each Inventory_File

### Requirement 3: Dashboard Display

**User Story:** As a User, I want to view comparison results in a web dashboard, so that I can quickly understand the matching status

#### Acceptance Criteria

1. THE Dashboard SHALL display Match_Percentage for each Inventory_File
2. THE Dashboard SHALL display the total number of records in Master_File
3. THE Dashboard SHALL display the total number of records in each Inventory_File
4. THE Dashboard SHALL display the number of matched records for each comparison
5. THE Dashboard SHALL display the number of mismatched records for each comparison
6. THE Dashboard SHALL display the number of missing records (exist in Master_File only)
7. THE Dashboard SHALL display the number of extra records (exist in Inventory_File only)
8. THE Dashboard SHALL highlight mismatches using color coding (green for match, red for mismatch, yellow for missing/extra)
9. THE Dashboard SHALL support Thai language for all labels and messages
10. WHEN a User clicks on a mismatch count, THE Dashboard SHALL display detailed mismatch records

### Requirement 4: Mismatch Report Generation

**User Story:** As a User, I want to generate Excel reports of mismatches, so that I can share and review them offline

#### Acceptance Criteria

1. WHEN a User requests a report, THE Report_Generator SHALL create an Excel file containing all mismatch records
2. THE Report_Generator SHALL include a summary sheet showing Match_Percentage and record counts
3. THE Report_Generator SHALL include separate sheets for each type of mismatch (field mismatches, missing records, extra records)
4. THE Report_Generator SHALL highlight mismatched cells using red background color
5. THE Report_Generator SHALL include both Master_File values and Inventory_File values side-by-side for comparison
6. THE Report_Generator SHALL include the comparison timestamp in the report
7. WHEN report generation is complete, THE Report_Generator SHALL provide a download link to the User
8. THE Report_Generator SHALL name the report file using the pattern: {Inventory_Type}_Mismatch_Report_{Date}_{Time}.xlsx

### Requirement 5: Data Correction and Re-comparison

**User Story:** As a User, I want to correct mismatched data and re-compare files, so that I can iteratively improve data quality

#### Acceptance Criteria

1. WHEN a User views mismatch details in Dashboard, THE Data_Corrector SHALL display an edit button for each mismatched record
2. WHEN a User clicks edit button, THE Data_Corrector SHALL display an inline edit form with current values
3. THE Data_Corrector SHALL allow User to edit values in both Master_File data and Inventory_File data
4. WHEN a User saves corrections, THE Data_Corrector SHALL validate the edited values
5. WHEN a User saves corrections, THE Data_Corrector SHALL update the in-memory data
6. THE Data_Corrector SHALL provide a "Re-compare" button after corrections are made
7. WHEN a User clicks "Re-compare", THE System SHALL run Comparison_Engine again with updated data
8. WHEN re-comparison is complete, THE Dashboard SHALL refresh to show updated Match_Percentage and mismatch counts
9. THE Data_Corrector SHALL provide an "Export Corrections" button to save corrected data to a new Excel file

### Requirement 6: Data Persistence

**User Story:** As a User, I want my uploaded files and corrections to be saved, so that I can return to continue my work later

#### Acceptance Criteria

1. WHEN a User uploads files, THE System SHALL store the files in a designated directory
2. THE System SHALL maintain a session for each User with uploaded files and comparison results
3. WHEN a User makes corrections, THE System SHALL save correction history with timestamp and changed fields
4. THE System SHALL allow User to download the corrected Master_File as a new Excel file
5. THE System SHALL allow User to download the corrected Inventory_File as new Excel files
6. WHEN a User returns to Dashboard, THE System SHALL display the most recent comparison session

### Requirement 7: Performance and Scalability

**User Story:** As a User, I want the system to process large Excel files efficiently, so that I can work with real-world data volumes

#### Acceptance Criteria

1. THE Comparison_Engine SHALL process Excel files containing up to 10,000 records within 30 seconds
2. THE Dashboard SHALL load and display comparison results within 3 seconds
3. THE Report_Generator SHALL generate a Mismatch_Report within 10 seconds for up to 1,000 mismatch records
4. THE System SHALL handle concurrent uploads from multiple Users without performance degradation

### Requirement 8: Error Handling and Validation

**User Story:** As a User, I want clear error messages when something goes wrong, so that I can understand and fix issues

#### Acceptance Criteria

1. IF a User uploads a file that exceeds 50MB, THEN THE System SHALL reject the file and display a size limit error message
2. IF a User uploads a file with missing required columns, THEN THE System SHALL display which columns are missing
3. IF a User uploads a non-Excel file, THEN THE System SHALL reject the file and display a format error message
4. IF the Comparison_Engine encounters an unexpected error, THEN THE System SHALL log the error details and display a user-friendly error message
5. IF the Report_Generator fails to create a report, THEN THE System SHALL display an error message with retry option
6. THE System SHALL validate that Asset_ID values are unique within each file before comparison
7. IF duplicate Asset_ID values are found, THEN THE System SHALL display a warning message listing the duplicate IDs
