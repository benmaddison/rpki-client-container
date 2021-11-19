import ipaddress
import os
import sys
import pathlib

from rpkimancer.cert import (EECertificate,
                             TACertificateAuthority,
                             CertificateAuthority)
from rpkimancer.sigobj import RouteOriginAttestation

ROOT_DIR = pathlib.Path(__file__).parent

TALS_DIR = ROOT_DIR / "tals"

CACHE_DIR = ROOT_DIR / "cache"
RSYNC_DIR = CACHE_DIR / "rsync"
TA_DIR = CACHE_DIR / "ta"

MAX_REPO_PER_TAL = 10


class CA(CertificateAuthority):
    def publish(self, *, pub_path, recursive=True, **kwargs):
        mft_file_list = list()
        parent_pub_path = os.path.join(pub_path, self.issuer.uri_path)
        with open(os.path.join(parent_pub_path, self.cert_path), "wb") as f:
            f.write(self.cert_der)
        local_pub_path = os.path.join(pub_path, self.uri_path)
        os.makedirs(os.path.join(local_pub_path, self.repo_path), exist_ok=True)
        with open(os.path.join(local_pub_path, self.crl_path), "wb") as f:
            f.write(self.crl_der)
        mft_file_list.append((os.path.basename(self.crl_path),
                              self.crl_der))
        for issuee in self.issued:
            if issuee is not self:
                if issuee.mft_entry is not None:
                    mft_file_list.append(issuee.mft_entry)
                if recursive is True:
                    issuee.publish(pub_path=pub_path,
                                   recursive=recursive,
                                   **kwargs)
        self.issue_mft(mft_file_list)
        with open(os.path.join(local_pub_path, self.mft_path), "wb") as f:
            f.write(self.mft.to_der())


class EECert(EECertificate):
    @property
    def base_uri(self):
        return self.issuer.base_uri

    @property
    def uri_path(self):
        return self.issuer.uri_path


class Roa(RouteOriginAttestation):
    ee_cert_cls = EECert


def subprefix(prefix, length, i):
    return list(prefix.subnets(new_prefix=length))[i]


def base_uri(name):
    return f"rsync://{name}.example.net/rpki"


def main():
    # create TA
    prefix_r = ipaddress.ip_network("2001:db8::/32")
    r = TACertificateAuthority(common_name="R",
                               base_uri=base_uri("r"),
                               ip_resources=[prefix_r])

    # create attacker CA and children
    prefix_x = ipaddress.ip_network("2001:db8:a::/48")
    x = CA(common_name="X",
           base_uri=base_uri("x"),
           issuer=r,
           ip_resources=[prefix_x])
    for i in range(MAX_REPO_PER_TAL):
        p = subprefix(prefix_x, 56, i)
        xx = CA(common_name=f"XX{i}",
                base_uri=base_uri(f"xx{i}"),
                issuer=x,
                ip_resources=[p])
        Roa(issuer=xx, as_id=64512+i, ip_address_blocks=[(p, None)])

    # create victim CA and child, with ROAs
    prefix_y = ipaddress.ip_network("2001:db8:b::/48")
    y = CA(common_name="Y",
           base_uri=base_uri("y"),
           issuer=r,
           ip_resources=[prefix_y])
    Roa(issuer=y, as_id=65000, ip_address_blocks=[(prefix_y, None)])
    prefix_yy = subprefix(prefix_y, 56, 0)
    yy = CA(common_name="YY",
            base_uri=base_uri("yy"),
            issuer=y,
            ip_resources=[prefix_yy])
    Roa(issuer=yy, as_id=65001, ip_address_blocks=[(prefix_yy, None)])

    r.publish(pub_path=RSYNC_DIR,
              tal_path=TALS_DIR)


if __name__ == "__main__":
    sys.exit(main())
