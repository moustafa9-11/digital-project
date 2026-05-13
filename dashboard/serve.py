#!/usr/bin/env python3
"""
Dashboard API Server for Digital Steganography Forensics
Provides JSON API endpoints for web dashboard
"""

import os
import json
import re
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import threading
import time

class ForensicAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        self.base_dir = directory or os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.base_dir)
        super().__init__(*args, directory=self.base_dir, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/results':
            self.send_api_response(self.get_forensic_results())
        elif parsed_path.path == '/':
            self.serve_file('index.html')
        else:
            # Try to serve static files
            file_path = parsed_path.path.lstrip('/')
            self.serve_file(file_path)
    
    def serve_file(self, filename):
        file_path = os.path.join(self.base_dir, filename)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
                
            # Determine content type
            if filename.endswith('.html'):
                content_type = 'text/html'
            elif filename.endswith('.css'):
                content_type = 'text/css'
            elif filename.endswith('.js'):
                content_type = 'application/javascript'
            else:
                content_type = 'text/plain'
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def send_api_response(self, data):
        """Send JSON response"""
        json_data = json.dumps(data, indent=2)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def get_forensic_results(self):
        """Parse all report files and return structured JSON"""
        project_root = self.project_root
        
        # Initialize result structure
        results = {
            'overall_stats': {},
            'detection_results': [],
            'entropy_data': {},
            'file_size_data': {},
            'extracted_payloads': [],
            'media_comparison': [],
            'stegexpose_results': {},
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Parse final report for overall stats
        final_report_path = os.path.join(project_root, 'reports', 'final_report.txt')
        if os.path.exists(final_report_path):
            results['overall_stats'] = self.parse_final_report(final_report_path)
        
        # Parse detection report for detailed results
        detection_report_path = os.path.join(project_root, 'reports', 'detection_report.txt')
        if os.path.exists(detection_report_path):
            detection_data = self.parse_detection_report(detection_report_path)
            results['detection_results'] = detection_data.get('files', [])
            results['media_comparison'] = detection_data.get('media_comparison', [])
            results['stegexpose_results'] = detection_data.get('stegexpose', {})
        
        # Parse entropy report
        entropy_report_path = os.path.join(project_root, 'reports', 'entropy_report.txt')
        if os.path.exists(entropy_report_path):
            results['entropy_data'] = self.parse_entropy_report(entropy_report_path)
        
        # Parse extraction report for payloads
        extraction_report_path = os.path.join(project_root, 'reports', 'extraction_report.txt')
        if os.path.exists(extraction_report_path):
            results['extracted_payloads'] = self.parse_extraction_report(extraction_report_path)
        
        # Get file size data from directories
        results['file_size_data'] = self.get_file_size_data(project_root)
        
        return results
    
    def parse_final_report(self, file_path):
        """Parse final report for overall statistics"""
        stats = {
            'total_files': 0,
            'stego_files_detected': 0,
            'payloads_extracted': 0,
            'detection_accuracy': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract total files
            files_match = re.search(r'Files analyzed\s*:\s*(\d+)\s*images,\s*(\d+)\s*audio,\s*(\d+)\s*video', content)
            if files_match:
                stats['total_files'] = sum(map(int, files_match.groups()))
            
            # Extract stego files
            stego_match = re.search(r'Stego images\s*:\s*(\d+)', content)
            if stego_match:
                stats['stego_files_detected'] = int(stego_match.group(1))
            
            # Extract payloads
            payload_match = re.search(r'Payloads found\s*:\s*(\d+)\s*image\s*\+\s*(\d+)\s*audio\s*\+\s*(\d+)\s*video', content)
            if payload_match:
                stats['payloads_extracted'] = sum(map(int, payload_match.groups()))
            
            # Extract accuracy
            accuracy_match = re.search(r'Image detection\s*:\s*(\d+)/(\d+)\s*stego images confirmed\s*\((\d+)%\s*accuracy\)', content)
            if accuracy_match:
                stats['detection_accuracy'] = int(accuracy_match.group(3))
                
        except Exception as e:
            print(f"Error parsing final report: {e}")
        
        return stats
    
    def parse_detection_report(self, file_path):
        """Parse detection report for file-by-file results"""
        data = {
            'files': [],
            'media_comparison': [],
            'stegexpose': {}
        }
        
        try:
            # Read as binary and decode with error handling
            with open(file_path, 'rb') as f:
                raw_content = f.read()
            
            # Try to decode as UTF-8, fallback to latin-1 if needed
            try:
                content = raw_content.decode('utf-8', errors='ignore')
            except:
                content = raw_content.decode('latin-1', errors='ignore')
            
            # Parse individual file results more robustly
            # Look for FILE: patterns more carefully
            file_pattern = r'FILE:\s*([^\n\r]+)[\r\n]+'
            file_matches = re.findall(file_pattern, content)
            
            # Get content blocks after each FILE
            file_blocks = re.split(r'FILE:\s*[^\n\r]+[\r\n]+', content)
            
            for i, filename in enumerate(file_matches):
                if i + 1 < len(file_blocks):
                    block_content = file_blocks[i + 1]
                    
                    # Clean filename
                    filename = filename.strip()
                    if not filename:
                        continue
                    
                    # Determine file type
                    file_type = 'unknown'
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                        file_type = 'image'
                    elif filename.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                        file_type = 'audio'
                    elif filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
                        file_type = 'video'
                    
                    # Determine status and detection method
                    status = 'UNKNOWN'
                    detection_method = 'N/A'
                    payload_preview = None
                    
                    # Check for status indicators in order of specificity
                    # First check for clean indicators
                    if 'No appended data detected' in block_content:
                        status = 'CLEAN'
                        detection_method = 'EOF Analysis'
                    elif 'Progressive DCT' in block_content:
                        status = 'CLEAN'
                        detection_method = 'Metadata Analysis'
                    # Then check for stego indicators
                    elif 'SUSPICIOUS:' in block_content:
                        status = 'STEGO'
                        detection_method = 'EOF Analysis'
                        # Extract payload preview
                        lines = block_content.split('\n')
                        for line in lines:
                            if 'SUSPICIOUS:' in line:
                                preview = line.replace('SUSPICIOUS:', '').strip()[:100]
                                if preview:
                                    payload_preview = preview
                                    break
                    elif 'JFIF Version' in block_content and 'Baseline DCT' in block_content:
                        status = 'STEGO'
                        detection_method = 'Metadata Analysis'
                    
                    # Only add if we have a valid filename and not a duplicate
                    if filename and filename not in [f['filename'] for f in data['files']]:
                        data['files'].append({
                            'filename': filename,
                            'type': file_type,
                            'status': status,
                            'detection_method': detection_method,
                            'payload_preview': payload_preview
                        })
            
            # Parse media comparison section
            media_match = re.search(r'CLEAN vs STEGO MEDIA COMPARISON\n-+\n([\s\S]+?)(?=\n\n|\Z)', content)
            if media_match:
                media_section = media_match.group(1)
                # Parse individual media comparisons
                audio_match = re.search(r'clean_audio\.mp3 vs stego_audio\.mp3\n\s*Size\s*:\s*clean=(\d+)\s*B\s*stego=(\d+)\s*B\s*delta=([+-]\d+)\s*B\n\s*Entropy\s*:\s*clean=([\d.]+)\s*stego=([\d.]+)\s*delta=([+-]\d\.\d+)', media_section)
                if audio_match:
                    data['media_comparison'].append({
                        'pair': 'Audio',
                        'clean_size': int(audio_match.group(1)),
                        'stego_size': int(audio_match.group(2)),
                        'delta': int(audio_match.group(3)),
                        'entropy_delta': audio_match.group(6),
                        'verdict': 'SUSPICIOUS' if int(audio_match.group(3)) > 0 else 'CLEAN'
                    })
                
                video_match = re.search(r'clean_video\.mp4 vs stego_video\.mp4\n\s*Size\s*:\s*clean=(\d+)\s*B\s*stego=(\d+)\s*B\s*delta=([+-]\d+)\s*B\n\s*Entropy\s*:\s*clean=([\d.]+)\s*stego=([\d.]+)\s*delta=([+-]\d\.\d+)', media_section)
                if video_match:
                    data['media_comparison'].append({
                        'pair': 'Video',
                        'clean_size': int(video_match.group(1)),
                        'stego_size': int(video_match.group(2)),
                        'delta': int(video_match.group(3)),
                        'entropy_delta': video_match.group(6),
                        'verdict': 'SUSPICIOUS' if int(video_match.group(3)) > 0 else 'CLEAN'
                    })
            
            # Parse StegExpose results
            stegexpose_match = re.search(r'STEGEXPOSE RESULTS\n-+\n([\s\S]+?)(?=\n\n|\Z)', content)
            if stegexpose_match:
                stegexpose_section = stegexpose_match.group(1)
                data['stegexpose'] = {
                    'status': 'completed',
                    'results': stegexpose_section.strip()
                }
            else:
                data['stegexpose'] = {
                    'status': 'not_run',
                    'results': 'StegExpose not executed'
                }
                
        except Exception as e:
            print(f"Error parsing detection report: {e}")
        
        return data
    
    def parse_entropy_report(self, file_path):
        """Parse entropy report for entropy values"""
        entropy_data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse entropy values
            lines = content.split('\n')
            for line in lines:
                match = re.match(r'(.+?)\s*->\s*Entropy:\s*([\d.]+)', line)
                if match:
                    filename = match.group(1).strip()
                    entropy = float(match.group(2))
                    entropy_data[filename] = entropy
                    
        except Exception as e:
            print(f"Error parsing entropy report: {e}")
        
        return entropy_data
    
    def parse_extraction_report(self, file_path):
        """Parse extraction report for extracted payloads"""
        payloads = []
        seen_filenames = set()  # Track seen filenames to avoid duplicates
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse extraction blocks
            blocks = re.split(r'\nFILE:\s*([^\n]+)', content)
            
            for i in range(1, len(blocks)):  # Skip first empty block
                if i >= len(blocks):
                    break
                filename = blocks[i].split('\n')[0].strip()
                block_content = blocks[i]
                
                # Check if extraction was successful
                status_match = re.search(r'Status\s*:\s*(\S+)', block_content)
                if status_match and status_match.group(1) == 'SUCCESS':
                    # Extract payload text
                    payload_match = re.search(r'Payload\s*:\n([\s\S]+?)(?=\n\n|\Z)', block_content)
                    extraction_method = 'Steghide' if 'steghide' in block_content.lower() else 'EOF Analysis'
                    
                    if payload_match:
                        payload_text = payload_match.group(1).strip()
                        payloads.append({
                            'source_filename': filename,
                            'extraction_method': extraction_method,
                            'payload_text': payload_text
                        })
                        seen_filenames.add(filename)
                        
        except Exception as e:
            print(f"Error parsing extraction report: {e}")
    
        return payloads
    
    def get_file_size_data(self, project_root):
        """Get file size data from dataset directories"""
        size_data = {}
        
        datasets_dir = os.path.join(project_root, 'datasets')
        
        # Check image pairs
        for i in range(1, 4):  # Assuming 3 pairs
            clean_file = os.path.join(datasets_dir, 'images', f'clean_{i}.jpg')
            stego_file = os.path.join(datasets_dir, 'images', f'stego_{i}.jpg')
            
            if os.path.exists(clean_file) and os.path.exists(stego_file):
                clean_size = os.path.getsize(clean_file)
                stego_size = os.path.getsize(stego_file)
                
                size_data[f'Image {i}'] = {
                    'clean_size': clean_size,
                    'stego_size': stego_size,
                    'delta': stego_size - clean_size
                }
        
        # Check audio pair
        clean_audio = os.path.join(datasets_dir, 'audio', 'clean_audio.mp3')
        stego_audio = os.path.join(datasets_dir, 'audio', 'stego_audio.mp3')
        
        if os.path.exists(clean_audio) and os.path.exists(stego_audio):
            clean_size = os.path.getsize(clean_audio)
            stego_size = os.path.getsize(stego_audio)
            
            size_data['Audio'] = {
                'clean_size': clean_size,
                'stego_size': stego_size,
                'delta': stego_size - clean_size
            }
        
        # Check video pair
        clean_video = os.path.join(datasets_dir, 'videos', 'clean_video.mp4')
        stego_video = os.path.join(datasets_dir, 'videos', 'stego_video.mp4')
        
        if os.path.exists(clean_video) and os.path.exists(stego_video):
            clean_size = os.path.getsize(clean_video)
            stego_size = os.path.getsize(stego_video)
            
            size_data['Video'] = {
                'clean_size': clean_size,
                'stego_size': stego_size,
                'delta': stego_size - clean_size
            }
        
        return size_data

def run_server():
    """Start dashboard server"""
    PORT = 8082
    
    print(f"Starting Digital Steganography Forensics Dashboard...")
    print(f"Server running on: http://localhost:{PORT}")
    print(f"API endpoint: http://localhost:{PORT}/api/results")
    print(f"Press Ctrl+C to stop server")
    
    with socketserver.TCPServer(("127.0.0.1", PORT), ForensicAPIHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()
