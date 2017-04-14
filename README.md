# ucdpv_vent_infrastructure

## Installing dependencies
To install all dependent packages the user first needs install virtualenv. Using
pip this can be done via

    pip install virtualenv

Then create a new virtual environment and activate it

    virtualenv venv
    source venv/bin/activate

Next navigate to the base directory where `setup.py` is. Run the following command

    pip install -e .
    python setup.py develop

Now all dependent packages should be installed

## Raspberry Pi Setup

### Via image flashing

### Via Ansible
If you have already setup your raspberry pi using NOOBS or some other tool and want
to modify your raspberry pi to collect ventilator data then setup via ansible may
be best.

#### Pre-setup
The requirements here are that a wireless network is set up and that the internal
network address of this network is known. If the internal network address is not
known then you can type in the command

    ifconfig

The network address should look something similiar to `192.168.1.10`. Here take
the first 3 numbers of this address and input it into `__init__.py` in the raspi
directory. Now enter the first 3 numbers in the address into the `lan_prefix`
variable name. For example if your address was `192.168.1.10` you would enter
`lan_prefix = "192.168.1"`.

#### Raspberry Pi minimal setup
Now that the provisioning LAN is setup, plug an ethernet cable from the router
into the raspberry pi. Navigate to the `raspi/ansible` directory and modify the
file at `group_vars/prod`. Here enter the production network's wireless SSID and
password. Also enter the network's ntp server host ip addresses. Finally
installation can proceed. To install all necessary software

    ansible-playbook -u pi --ask-sudo -i inventory/rpi_initial rpi_minimal_install.yml

When prompted for the password enter "raspberry" per standard setup. After
ansible finishes your raspberry pi will be able to collect ventilator waveform data!

## Clinicalsupervisor Setup
Activate your virtual environment, navigate to `raspi/ansible`. Create a new
inventory script using `inventory/ucd` as an example. Input the host DNS name
under the `[clinicalsupervisor]` group.

### OSX

    ansible-playbook -i inventory/<inv file name> clinicalsupervisor_install_osx.yml

### Debian

    ansible-playbook -i inventory/<inv file name> clinicalsupervisor_install_debian.yml
