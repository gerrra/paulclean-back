#!/usr/bin/env python3
"""
Simple SMTP server for testing email functionality
Compatible with Python 3.13+
"""

import socket
import threading
import time
import email
from email import policy
import base64

class SimpleSMTPServer:
    def __init__(self, host='localhost', port=1025):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        
    def start(self):
        """Start the SMTP server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"🚀 SMTP Server started on {self.host}:{self.port}")
        print("📧 All emails will be displayed in console")
        print("🛑 Press Ctrl+C to stop")
        
        try:
            while self.running:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down SMTP server...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the SMTP server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("✅ SMTP server stopped")
    
    def handle_client(self, client_socket, address):
        """Handle SMTP client connection"""
        try:
            # Send welcome message
            self.send_response(client_socket, "220 localhost SMTP Test Server")
            
            # Simple SMTP conversation
            while self.running:
                data = client_socket.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    break
                
                command = data.strip().upper()
                
                if command.startswith('EHLO') or command.startswith('HELO'):
                    self.send_response(client_socket, "250 localhost")
                elif command.startswith('MAIL FROM:'):
                    self.send_response(client_socket, "250 OK")
                elif command.startswith('RCPT TO:'):
                    self.send_response(client_socket, "250 OK")
                elif command == 'DATA':
                    self.send_response(client_socket, "354 End data with <CR><LF>.<CR><LF>")
                    self.receive_email_data(client_socket)
                elif command == 'QUIT':
                    self.send_response(client_socket, "221 Bye")
                    break
                else:
                    self.send_response(client_socket, "500 Command not recognized")
                    
        except Exception as e:
            print(f"❌ Error handling client {address}: {e}")
        finally:
            client_socket.close()
    
    def send_response(self, client_socket, response):
        """Send SMTP response to client"""
        try:
            client_socket.send(f"{response}\r\n".encode('utf-8'))
        except:
            pass
    
    def receive_email_data(self, client_socket):
        """Receive and process email data"""
        email_data = ""
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    break
                
                email_data += data
                
                # Check for end of data marker
                if email_data.endswith('\r\n.\r\n'):
                    break
            
            # Remove end marker
            email_data = email_data.replace('\r\n.\r\n', '')
            
            # Process the email
            self.process_email(email_data)
            
            # Send success response
            self.send_response(client_socket, "250 OK")
            
        except Exception as e:
            print(f"❌ Error receiving email data: {e}")
            self.send_response(client_socket, "500 Error")
    
    def process_email(self, email_data):
        """Process received email data"""
        try:
            # Parse email using email module
            msg = email.message_from_string(email_data, policy=policy.default)
            
            print(f"\n📧 EMAIL RECEIVED:")
            print(f"From: {msg.get('From', 'Unknown')}")
            print(f"To: {msg.get('To', 'Unknown')}")
            print(f"Subject: {msg.get('Subject', 'No Subject')}")
            print(f"Date: {msg.get('Date', 'Unknown')}")
            
            # Extract text content
            text_content = ""
            html_content = ""
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        text_content = part.get_content()
                    elif content_type == "text/html":
                        html_content = part.get_content()
            else:
                content_type = msg.get_content_type()
                if content_type == "text/plain":
                    text_content = msg.get_content()
                elif content_type == "text/html":
                    html_content = msg.get_content()
            
            if text_content:
                print(f"\n📝 Text Content:")
                print(text_content)
            
            if html_content:
                print(f"\n🌐 HTML Content:")
                print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
            
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Error processing email: {e}")
            print(f"Raw data: {email_data[:200]}...")

def main():
    """Main function to start SMTP server"""
    server = SimpleSMTPServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    finally:
        server.stop()

if __name__ == "__main__":
    main()
