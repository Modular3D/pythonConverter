from flask import Flask, request, jsonify, send_file, after_this_request
import aspose.threed as a3d
import os
import tempfile
import shutil

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_usdz_to_glb():
    # Check if the request contains a file named 'usdz'
    if 'usdz' not in request.files:
        return jsonify({'error': 'USDZ file is required'}), 400
    
    # Get the USDZ file from the request
    usdz_file = request.files['usdz']
    
    # Save the uploaded file to a temporary location
    temp_dir = tempfile.mkdtemp()
    temp_usdz_file_path = os.path.join(temp_dir, 'temp.usdz')
    usdz_file.save(temp_usdz_file_path)
    
    # Load the USDZ file and convert it to GLB
    scene = a3d.Scene.from_file(temp_usdz_file_path)
    output_glb_file_path = os.path.join(temp_dir, 'output.glb')
    scene.save(output_glb_file_path)
    
    # Send the converted GLB file back to the client
    @after_this_request
    def remove_files(response):
        try:
            os.remove(temp_usdz_file_path)
            os.remove(output_glb_file_path)
            os.rmdir(temp_dir)
        except Exception as e:
            app.logger.error(f"Error deleting files: {e}")
        return response

    return send_file(output_glb_file_path, as_attachment=True)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'message': 'Backend is working'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)