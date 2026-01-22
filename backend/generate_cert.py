"""
Generate self-signed SSL certificates for local development
"""
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta
import os

def generate_self_signed_cert():
    """Generate self-signed SSL certificate for localhost"""
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Generate certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Localhost"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NeuroWell-CA"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("127.0.0.1"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Create certs directory if it doesn't exist
    certs_dir = os.path.join(os.path.dirname(__file__), 'certs')
    os.makedirs(certs_dir, exist_ok=True)
    
    # Write private key
    key_path = os.path.join(certs_dir, 'key.pem')
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Write certificate
    cert_path = os.path.join(certs_dir, 'cert.pem')
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print(f"✅ SSL certificates generated successfully!")
    print(f"   Certificate: {cert_path}")
    print(f"   Private Key: {key_path}")
    print(f"   Valid for: 365 days")
    print(f"\n⚠️  Note: This is a self-signed certificate for development only.")
    print(f"   Your browser will show a security warning. Click 'Advanced' and 'Proceed to localhost'.")

if __name__ == '__main__':
    generate_self_signed_cert()
