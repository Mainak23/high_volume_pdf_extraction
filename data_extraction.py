import pdfplumber
from wand.image import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
import os
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
import json
import re
import time
import logging
import json
import gc
from datetime import datetime
import shutil


# Get the current date and time
current_time = datetime.now()

class ocr_complete:
    folder_name = 'split_pdf'
    secondary_folder = 'convert_files'
    out_folder="output"
    final_output="final_output"
    os.makedirs(final_output,exist_ok=True)
    os.makedirs(folder_name,exist_ok=True)
    os.makedirs(secondary_folder,exist_ok=True)
    os.makedirs(out_folder,exist_ok=True)

    @classmethod
    def split_pdf_by_pages_complete(cls,pdf_path):
        # Open the PDF file
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        print(f"Total number of pages: {num_pages}")
        # Split and save each page
        for page_num in range(num_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
            # Output file name
            output_filename = os.path.join(cls.folder_name, f"page_{page_num+1}.pdf")
            # Write the single page to a new PDF file
            with open(output_filename, "wb") as output_file:
                writer.write(output_file)
            print(f"Saved: {output_filename}")
        

    @classmethod
    def split_pdf_by_pages(cls, pdf_path, page_num):
        # Open the PDF file
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        if page_num >= num_pages:
            print(f"Page number {page_num} exceeds the total number of pages ({num_pages}).")
            return
        print(f"Total number of pages: {num_pages}")
        # Split and save the specified page
        writer = PdfWriter()
        writer.add_page(reader.pages[page_num])
        # Output file name for the specific page
        output_filename = os.path.join(cls.folder_name, f"page_{page_num}.pdf")

        # Write the single page to a new PDF file
        with open(output_filename, "wb") as output_file:
            writer.write(output_file)
            print(f"Saved: {output_filename}")

    @classmethod
    def arrange_file(cls):
        file_list = os.listdir(cls.folder_name)
        print(f"Files in '{cls.folder_name}': {file_list}")
        # Filter JPEG files
        jpg_files = [file for file in file_list if file.lower().endswith('.pdf')]
        # Create a list of tuples (file_name, creation_time)
        file_creation_times = []
        for file in jpg_files:
            file_path = os.path.join(cls.folder_name, file)
            creation_time = os.path.getctime(file_path)
            file_creation_times.append((file, creation_time))
        # Sort files by creation time
        sorted_files = sorted(file_creation_times, key=lambda x: x[1])
        page_names = [file_name for file_name, _ in sorted_files]
        # Print sorted files
        print("Files sorted by creation time:")
        for file, creation_time in sorted_files:
            creation_time_formatted = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{file}: {creation_time_formatted}")
        pdf_files=[os.path.join(cls.folder_name,page_names[i]) for i in range(len(page_names))]
        return pdf_files
    
    @classmethod
    def convert(cls,pdf_path):
        output_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        png_path = os.path.join(cls.secondary_folder,output_filename + '.png')
        ocr_path = os.path.join(cls.secondary_folder,output_filename + '-ocr.pdf')
        try:  # Convert PDF to PNG(s) for the first page only
            with Image(filename=pdf_path, resolution=300) as img:
                with img.convert('png') as converted:
                    converted.compression_quality = 99
                    converted.save(filename=png_path)
                # Perform OCR on the first PNG and convert to PDF with OCR data
                extracted_text = pytesseract.image_to_pdf_or_hocr(png_path, lang='eng', config='--psm 1')
                # Save OCR'd PDF
                with open(ocr_path, 'wb') as ocr_file:
                    ocr_file.write(extracted_text)
                    print('OCR conversion completed for: ' + pdf_path)
        except Exception as e:
                #raise HTTPException(status_code= 500 ,detail="Process failed"+str(e))
                print('Error message:', str(e))
            # Delete temporary PNG file
        if os.path.exists(png_path):
            os.remove(png_path)
            print('Temporary PNG file deleted.')
            return ocr_path
    @classmethod
    def extract_tables_from_pdf_all(cls,pdf_path):
        table_settings = {
                    "vertical_strategy": "lines_strict",      # How to detect vertical lines (e.g., 'lines', 'text')
                    "horizontal_strategy": "lines"}
        dict_text={}
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text( )
                #print(f"Page {page_num}")
                if text:
                    dict_text[f'page_{page_num}'] = text
                    try:
                        tables = page.extract_tables(table_settings=table_settings)
                        if tables:
                            for table_num, table in enumerate(tables, start=1):
                                dict_text[f"Page_{page_num}"]={f"table_{table_num}":tables}
                                #print(dict_text)
                        else:
                            dict_text[f"Page_{page_num}"]={f"table_{table_num}":"No table found on this page"}
                    except Exception:
                        print("no_table_found")
                else:
                    dict_text[f'page_{page_num}'] ="likely image-based."
        json_data = json.dumps(dict_text, indent=4)   # `indent=4` for pretty printing
        base_pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    # Define the output path for the JSON file
        output_json_path = os.path.join(cls.out_folder,f"{base_pdf_name}_output.json")
        with open(output_json_path, 'w') as json_file:
            json.dump(dict_text, json_file, indent=4)
        return json_data, output_json_path

    @classmethod
    def extract_tables_from_pdf(cls,pdf_path):
        # Table extraction settings
        page_number = str((re.search(r'page_(\d+)', pdf_path)).group(0))
        table_settings = {
            "vertical_strategy": "lines_strict",  # Strategy for detecting vertical lines
            "horizontal_strategy": "lines"        # Strategy for detecting horizontal lines
        }
        dict_text = {}
        # Open the PDF and process only the first page
        with pdfplumber.open(pdf_path) as pdf:
            # Ensure there's at least one page
            if len(pdf.pages) > 0:
                page = pdf.pages[0]  # Extract the first page
                text = page.extract_text()
                # Add extracted text to the dictionary
                dict_text[page_number] = {'text': text if text else "No text extracted"}
                # Try to extract tables from the first page
                try:
                    tables = page.extract_tables(table_settings=table_settings)
                    if tables:
                        dict_text[page_number]['tables'] = {f"table_1": tables}
                    else:
                        dict_text[page_number]['tables'] = "No tables found on this page"
                except Exception as e:
                    dict_text[page_number]['tables'] = "Error extracting tables: " + str(e)
            else:
                dict_text[page_number] = "No pages found in the PDF"
        # Save the extracted data to a JSON file
        return dict_text


class file_handler:
    final_output="final_output"
    #os.makedirs(final_output,exist_ok=True)
    @staticmethod
    def read_json_file(file_path):
        try:
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
                filter_ed={key: value for key, value in data.items() if value=="likely image-based."}
                extract_keys=[int(string.split('_')[1]) for string in  filter_ed.keys()]
                return extract_keys
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except json.JSONDecodeError:
            print("Error decoding JSON")
        return None
    @staticmethod
    def combine_file(file_path_2,file_path,path):
        with open(file_path_2, 'r') as json_file:
            data_1 = json.load(json_file)
        page_dict = {key: value for i in range(len(data_1)) for key, value in data_1[i].items()}
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
            filter_ed={key: value for key, value in data.items() if value=="likely image-based."}
            extract_keys=[string for string in  filter_ed.keys()]
        for i in extract_keys:
            data[i]=page_dict[i]
        base_pdf_name = os.path.splitext(os.path.basename(path))[0]
        output_json_path = os.path.join("final_output",f"{base_pdf_name}_final_output.json")
        with open(output_json_path, 'w') as output_json:
            json.dump(data, output_json, indent=4)
            print(f"Combined JSON data written to {output_json_path}")
        return output_json_path
    @staticmethod
    def delete_files_in_directory(directory):
        if os.path.exists(directory):
            # Iterate through all items in the directory
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                # Check if it is a file, not a directory
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Delete the file
                    print(f"Deleted file: {file_path}")
                elif os.path.isdir(file_path):
                    print(f"Skipping directory: {file_path}")
            print(f"All files in {directory} have been deleted.")
        else:
            print(f"Directory not found: {directory}")
    @staticmethod
    def read_json(path):
        with open(path, 'r') as output_json:
            data = json.load(output_json)
        return data


# Example usage
logging.basicConfig(filename='execution_time.log', level=logging.INFO,format='%(asctime)s|%(levelname)-8s| %(filename)s:%(lineno)d| %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
def final_out_put(pdf_path):
    json_path=""
    try:
        logging.info(f"################### process for {pdf_path} started at {current_time}.#####################")
        
        start_extract_all = time.perf_counter()
        _, complete_path = ocr_complete.extract_tables_from_pdf_all(pdf_path)
        time.sleep(2)  # Simulate delay for extraction
        
        end_extract_all = time.perf_counter()
        logging.info("Extract all text from pdf file at once done in: %s seconds", int(end_extract_all - start_extract_all))

        logging.info("Check for any page of the pdf that is image-based")
        file_path = [os.path.join("output", file) for file in os.listdir("output") if file.endswith('.json')][0]
        list_number = file_handler.read_json_file(file_path)
        
        if len(list_number) > 0:
            logging.info("Count of image-based pages: %s", len(list_number))

            # Split PDF pages
            start_split_all = time.perf_counter()
            [ocr_complete.split_pdf_by_pages(pdf_path, page_num - 1) for page_num in list_number]
            time.sleep(2)
            end_split_all = time.perf_counter()
            logging.info("Split image-based pages of the PDF in: %s seconds", int(end_split_all - start_split_all))

            path_list = [os.path.join("split_pdf", file) for file in os.listdir("split_pdf")]

            # Convert split PDFs
            start_convert_all = time.perf_counter()
            [ocr_complete.convert(pdf_path) for pdf_path in path_list]
            time.sleep(2)
            end_convert_all = time.perf_counter()
            logging.info("Converted all split PDFs in: %s seconds", int(end_convert_all - start_convert_all))

            path_list_converted_pdf = [os.path.join("convert_files", file) for file in os.listdir("convert_files")]

            # Extract tables from converted PDFs
            start_extract = time.perf_counter()
            data = [ocr_complete.extract_tables_from_pdf(path) for path in path_list_converted_pdf]
            time.sleep(2)
            end_extract = time.perf_counter()
            logging.info("Extracted tables from converted PDFs in: %s seconds", int(end_extract - start_extract))
            # Store the output in JSON
            base_pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_json_path = os.path.join("output", f"{base_pdf_name}_converted_output.json")
            with open(output_json_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            logging.info("Stored the final output in JSON")
            # Combine files
            file_handler.combine_file(output_json_path, complete_path, pdf_path)
            # Cleanup unnecessary files
            output_copy_path=shutil.copy(complete_path, "final_output")
            logging.info("Deleting unnecessary files")
            file_handler.delete_files_in_directory("convert_files")
            file_handler.delete_files_in_directory("split_pdf")
            file_handler.delete_files_in_directory("output")
            json_path+=output_copy_path
            logging.info(f"##########################process for {pdf_path} end ###############################")
        else:
            logging.info("no image-based pages found")
            logging.info("Stored the final output in JSON")
            output_copy_path=shutil.copy(complete_path, "final_output")
            json_path+=output_copy_path
            logging.info("No image-based pages found. Cleaning up files.")
            file_handler.delete_files_in_directory("output")
            logging.info(f"##########################process for {pdf_path} end ###############################")
    except Exception as e:
        logging.error("An error occurred in processing %s: %s", pdf_path, str(e))
        logging.exception("Exception details:")  # This logs the full traceback
    finally:
        # Ensure memory is always released, even on error
        logging.info("Releasing memory in final cleanup")
        file_handler.delete_files_in_directory("uploads")
        gc.collect()
    return json_path

import chromadb
def store_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    db_path = os.path.join(os.getcwd(), "input_storage", "data_base")
    collection_name="my_collection"
    os.makedirs(db_path)
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name=collection_name)
    for key,value in data.items():
            collection.add(
                documents=value,
                ids=key
                )
            print(f"Added documents to the collection.")
    time.sleep(0.5)

    results = collection.query(query_texts=[" "],where_document={"$contains": "Monthly Transmission Charges for Designated ISTS Customers"})["ids"][0]
    client.delete_collection(collection_name)
    print(results)
    return results




filename=r"RTA0924.pdf"
file_path=final_out_put(filename)
print(file_path)
#store_data(file_path)



