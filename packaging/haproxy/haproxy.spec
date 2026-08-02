%global debug_package %{nil}
%global upstream_name haproxy

Name:           sister-haproxy-lab
Version:        3.2.22
Release:        1.sistersec03v%{?dist}
Summary:        Native HAProxy build for the SisTer SEC-03V candidate laboratory
License:        GPL-2.0-or-later AND LGPL-2.1-or-later
URL:            https://www.haproxy.org/
Source0:        https://www.haproxy.org/download/3.2/src/haproxy-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  libxcrypt-devel
BuildRequires:  make
BuildRequires:  openssl-devel
BuildRequires:  pcre2-devel
ExclusiveArch:  x86_64

%description
Native, laboratory-scoped HAProxy build used only by the governed SisTer
SEC-03V candidate environment. This package installs no configuration, user,
network listener, container wrapper, or generic systemd unit.

%prep
%autosetup -n %{upstream_name}-%{version}

%build
%make_build \
  TARGET=linux-glibc \
  EXTRAVERSION=-sister-sec03v.1 \
  USE_OPENSSL=1 \
  USE_PCRE2=1 \
  USE_PROMEX=1 \
  CC=%{__cc} \
  CFLAGS="%{build_cflags}" \
  LDFLAGS="%{build_ldflags}" \
  OPT_CFLAGS="" ARCH_FLAGS="" \
  DEFINE=-DMAX_SESS_STKCTR=5

%check
./haproxy -vv | grep -F "HAProxy version %{version}"
./haproxy -h 2>&1 | grep -F -- "-Ws master-worker mode with systemd notify support."
./haproxy -vv | grep -F "+OPENSSL"
./haproxy -vv | grep -F "+PCRE2"

%install
install -D -p -m 0755 haproxy \
  %{buildroot}/usr/local/sbin/haproxy-%{version}

%files
%license LICENSE doc/gpl.txt doc/lgpl.txt
%doc CHANGELOG README.md INSTALL
/usr/local/sbin/haproxy-%{version}

%changelog
* Sun Aug 02 2026 SisTer SEC-03V Lab <noreply@sister.local> - 3.2.22-1.sistersec03v
- Initial native package for the restricted SEC-03V candidate laboratory.
