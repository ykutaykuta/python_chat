"""
Certificate generation module.
"""

from pathlib import Path

from OpenSSL import crypto

TYPE_RSA = crypto.TYPE_RSA
TYPE_DSA = crypto.TYPE_DSA


def createKeyPair(key_type, bits):
    """
    Create a public/private key pair.
    Arguments: key_type - Key key_type, must be one of TYPE_RSA and TYPE_DSA
               bits - Number of bits to use in the key
    Returns:   The public/private key pair in a PKey object
    """
    pkey = crypto.PKey()
    pkey.generate_key(key_type, bits)
    return pkey


def createCertRequest(pkey, digest="md5", **name):
    """
    Create a certificate request.
    Arguments: pkey   - The key to associate with the request
               digest - Digestion method to use for signing, default is md5
               **name - The name of the subject of the request, possible
                        arguments are:
                          C     - Country name
                          ST    - State or province name
                          L     - Locality name
                          O     - Organization name
                          OU    - Organizational unit name
                          CN    - Common name
                          emailAddress - E-mail address
    Returns:   The certificate request in an X509Req object
    """
    req = crypto.X509Req()
    subj = req.get_subject()

    for (key, value) in name.items():
        setattr(subj, key, value)

    req.set_pubkey(pkey)
    req.sign(pkey, digest.encode())
    return req


def createCertificate(req, issuerCert, issuerKey, serial, notBefore, notAfter, digest="md5"):
    """
    Generate a certificate given a certificate request.
    Arguments: req        - Certificate reqeust to use
               issuerCert - The certificate of the issuer
               issuerKey  - The private key of the issuer
               serial     - Serial number for the certificate
               notBefore  - Timestamp (relative to now) when the certificate
                            starts being valid
               notAfter   - Timestamp (relative to now) when the certificate
                            stops being valid
               digest     - Digest method to use for signing, default is md5
    Returns:   The signed certificate in an X509 object
    """
    cert = crypto.X509()
    cert.set_serial_number(serial)
    cert.gmtime_adj_notBefore(notBefore)
    cert.gmtime_adj_notAfter(notAfter)
    cert.set_issuer(issuerCert.get_subject())
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(issuerKey, digest.encode())
    return cert


def gen_cert(name: str = "server"):
    curr_path = Path().resolve()
    pkey_file = curr_path.joinpath(f"{name}.pkey")
    cert_file = curr_path.joinpath(f"{name}.cert")
    if pkey_file.exists() and cert_file.exists():
        return

    ca_key = createKeyPair(TYPE_RSA, 1024)
    ca_req = createCertRequest(ca_key, CN='Certificate Authority')
    ca_cert = createCertificate(ca_req, ca_req, ca_key, 0, 0, 60 * 60 * 24 * 365 * 5)  # five years
    open('CA.pkey', 'w').write(crypto.dump_privatekey(crypto.FILETYPE_PEM, ca_key).decode())
    open('CA.cert', 'w').write(crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert))

    pkey = createKeyPair(TYPE_RSA, 1024)
    req = createCertRequest(pkey, CN=name)
    cert = createCertificate(req, ca_cert, ca_key, 1, 0, 60 * 60 * 24 * 365 * 5)  # five years
    open(str(pkey_file), 'w').write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey).decode())
    open(str(cert_file), 'w').write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
