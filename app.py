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
    
    # Compress the GLB file using the KTX API
    with open(output_glb_file_path, 'rb') as glb_file:
        files = {'model': (output_glb_file_path, glb_file, 'model/gltf-binary')}
        ktx_response = requests.post('https://api.modularcx.link/conversion/ktx/ktx-compression', files=files)
        
    if ktx_response.status_code != 200:
        app.logger.error(f"Failed to compress GLB file. Status code: {ktx_response.status_code}, Response: {ktx_response.text}")
        return jsonify({'error': 'Failed to compress GLB file', 'details': ktx_response.text}), 500

    # Save the compressed GLB file
    compressed_glb_file_path = f'{original_base_name}-compressed.glb'
    with open(compressed_glb_file_path, 'wb') as compressed_file:
        compressed_file.write(ktx_response.content)

    # Convert the compressed GLB back to USDZ
    compressed_scene = a3d.Scene.from_file(compressed_glb_file_path)
    output_usdz_file_path = f'{original_base_name}-compressed.usdz'
    compressed_scene.save(output_usdz_file_path)
    
    # Define form data for S3 upload
    form_data = {
        'bucketName': 'morphobucket',
        'folderName': 'iosapp'
    }
    
    # Upload both the compressed USDZ file and the compressed GLB file to S3
    with open(output_usdz_file_path, 'rb') as usdz_file, open(compressed_glb_file_path, 'rb') as compressed_glb_file:
        files = [
            ('file', (output_usdz_file_path, usdz_file, 'model/vnd.usdz+zip')),
            ('file', (compressed_glb_file_path, compressed_glb_file, 'model/gltf-binary'))
        ]
        response = requests.post('https://api.modularcx.link/global-functions-api/s3/upload-to-s3', data=form_data, files=files)
    
    # Delete the temporary files after the request is complete
    @after_this_request
    def remove_files(response):
        try:
            os.remove(temp_usdz_file_path)
            os.remove(output_glb_file_path)
            os.remove(compressed_glb_file_path)
            os.remove(output_usdz_file_path)
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
#test