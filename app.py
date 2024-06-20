from flask import Flask, request, jsonify, after_this_request, Blueprint
import aspose.threed as a3d
import os
import requests

app = Flask(__name__)

# Define a blueprint for the converter routes
converter_bp = Blueprint('converter', __name__)

@converter_bp.route('/usdz-glb', methods=['POST'])
def convert_usdz_to_glb():
    # Check if the request contains a file named 'usdz'
    if 'usdz' not in request.files:
        return jsonify({'error': 'USDZ file is required'}), 400
    
    # Get the USDZ file from the request
    usdz_file = request.files['usdz']
    original_filename = usdz_file.filename
    original_base_name = os.path.splitext(original_filename)[0]
    
    # Save the uploaded file to a temporary location
    temp_usdz_file_path = f'{original_base_name}.usdz'
    usdz_file.save(temp_usdz_file_path)
    
    # Load the USDZ file and convert it to GLB
    scene = a3d.Scene.from_file(temp_usdz_file_path)
    output_glb_file_path = f'{original_base_name}.glb'
    scene.save(output_glb_file_path)
    
    # Define form data for S3 upload
    form_data = {
        'bucketName': 'morphobucket',
        'folderName': 'iosapp'
    }
    
    # Upload both the uploaded USDZ file and the output GLB file to S3
    with open(temp_usdz_file_path, 'rb') as original_file, open(output_glb_file_path, 'rb') as converted_file:
        files = [
            ('file', (temp_usdz_file_path, original_file, 'model/vnd.usdz+zip')),
            ('file', (output_glb_file_path, converted_file, 'model/gltf-binary'))
        ]
        response = requests.post('https://api.modularcx.link/global-functions-api/s3/upload-to-s3', data=form_data, files=files)
    
    # Delete the temporary files after the request is complete
    @after_this_request
    def remove_files(response):
        try:
            os.remove(temp_usdz_file_path)
            os.remove(output_glb_file_path)
        except Exception as e:
            app.logger.error(f"Error deleting files: {e}")
        return response
    
    # Check if the upload was successful
    if response.status_code == 200:
        # Return the response from the API we called
        return jsonify(response.json()), response.status_code
    else:
        app.logger.error(f"Failed to upload file to S3. Status code: {response.status_code}, Response: {response.text}")
        return jsonify({'error': 'Failed to upload file to S3', 'details': response.text}), 500

@converter_bp.route('/main', methods=['GET'])
def main_route():
    return "main route"

# Register the blueprint with the app
app.register_blueprint(converter_bp, url_prefix='/converter')

if __name__ == '__main__':
    app.run(debug=True)
