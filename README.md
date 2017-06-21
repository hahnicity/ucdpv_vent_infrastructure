# ucdpv_vent_infrastructure
The [UCDPV vent infrastructure][1] is designed to allow anyone to use off the shelf
commercial products to set up a fully functional clinical informatics study
for collecting of mechanical ventilator data.

In this README installation and usage instructions are provided.

## Installing dependencies
To install all dependent packages the user first needs install virtualenv. Using
pip this can be done via

    pip install virtualenv

Then create a new virtual environment and activate it

    virtualenv venv
    source venv/bin/activate

Next navigate to the root directory where `setup.py` is. Run the following command

    pip install -e .
    python setup.py develop

Now all dependent packages should be installed

## Raspberry Pi Setup

### Via image flashing
The first step in image flashing is to get an SD card reader/writer device. Hook
it up to your computer and then insert the raspberry pi's SD card into the
device.

You can [obtain the image here][2].

#### From Debian
From a debian based machine download the image then run the following command

    dd if=ucdpv-jessie.img bs=4M of=/dev/sdb

After this remove the SD card from the device and insert it into the raspberry pi
to boot.

#### From OSX
Setup is relatively the same as in Debian based machines here except the `of` input
will be different

    dd if=ucdpv-jessie.img bs=4M of=/dev/rdisk2s2

#### Final configuration
##### Network Operations and NTP Setup
It is important to note that without a connection to an NTP server ventilator data collection
will **NOT** commence. At UCD NetOps necessitated the RPi devices be located
behind a secure firewall. If this is the case with you after consulting with NetOps then
internet access to public NTP servers may not be available. If this is not the pertinent to your
institution then this section is unnecessary.

If there are network restrictions present on the wifi network then specific NTP servers
will need to be used. Go to `/etc/ntp.conf` and modify the file so that the NTP
server addresses, specific to your institution, are used. Configuration should look like

    server <host1 ip addr> iburst
    server <host2 ip addr> iburst

##### Wifi
The wifi network being used will need to be modified in `/etc/wpa_supplicant/wpa_supplicant.conf`.
Modify the file like so

    network={
        ssid=<WiFi SSID>
        psk=<WiFi password>
    }

Then, on the command line, restart the networking service to gain wifi connectivity

    sudo service network restart

##### Ethernet
No additional configuration is required here other than hooking an ethernet cable
to the raspberry pi.

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
the first 3 numbers of this address and open the file `raspi/__init__.py`

    nano raspi/__init__.py

Now enter the first 3 numbers in the address into the `lan_prefix`
variable name. For example if your address was `192.168.1.10` you would enter
`lan_prefix = "192.168.1"`.

#### Raspberry Pi minimal setup
Since Ansible was installed in previous steps and the provisioning LAN is now setup,
plug an ethernet cable from the router into the raspberry pi. Navigate
to the `raspi/ansible` directory

    cd raspi/ansible

and modify the file at `group_vars/rpis`.
Here enter the production network's wireless SSID and password.
Also enter the network's ntp server host ip addresses. Finally
installation can proceed. To install all necessary software

    ansible-playbook -u pi --ask-sudo -i inventory/rpi_initial rpi_minimal_install.yml

When prompted for the password enter "raspberry" per standard setup. After
ansible finishes your raspberry pi will be able to collect ventilator waveform data!

## Clinicalsupervisor Setup
Activate your virtual environment, navigate to `raspi/ansible`. Create a new
inventory script using `inventory/ucd` as an example. Input the host DNS name
under the `[clinicalsupervisor]` group.

If the database plugin is desired for use then the installer will need to modify
the file `group_vars/clinicalsupervisor` and the variables `database_host` and
`database_password`. To ensure these variables stay secret it is highly recommended
to use `ansible-vault` to encrypt this file so that secure information is not
gained by unauthorized parties. Information on how to use `ansible-vault` is located
[here][3].

### Static DNS
The clinicalsupervisor is able to communicate with the raspberry pi's through either
regular or static DNS. If for some reason the raspberry pi's are unable to be listed
in an institution DNS server or DNS is spotty then static DNS will need to be used.
Static DNS addresses can be provided to the clinicalsupervisor through the
`group_vars/clinicalsupervisor` file. If you are using static DNS but a raspberry pi
is not listed, then regular DNS will be used. Static addresses can be added like
this:

    static_dns:
        hostname1: 192.168.1.5
        hostname2: 192.168.1.6
        ...

### OSX

    ansible-playbook -i inventory/<inv file name> clinicalsupervisor_install_osx.yml

### Debian

    ansible-playbook -i inventory/<inv file name> clinicalsupervisor_install_debian.yml

## Usage

### Raspberry Pi
To use the raspberry pis, first get a micro-usb power cable and usb-to-RS232 serial
cable. Take the raspberry pi with these components to the ventilator and hook the RS232 cable to the
the primary serial port of the PB-840 ventilator and the usb side to the raspberry pi. Power
the raspberry pi with the power cable, and ensure the ventilator is currently
operating. Once the ventilator is operating waveform data collection will begin.

### Clinicalsupervisor
There are several pieces of functionality that the clinicalsupervisor utilizes
to perform its job.

1. Listing files
2. Backing up files
3. Deleting files
4. Gather patient data

In each case the clinicalsupervisor asks for an input of the raspberry pi name
before continuing. The raspberry pi name is the DNS name for the device on the
network. If this has not been created but the pi's are connected to the network
and have a static ip address then a static DNS service hosted by the clinicalsupervisor
can be used. For details about setting this up go to the section on `Static DNS`
in the installation guide.

#### Listing files
If the user desires to know the filenames on a raspberry pi then the `List` button
on the top nav bar will allow this.

#### Backing up files
This will perform a backup of all files currently on the raspberry pi. Use the
`Backups` button on the nav bar for this.

#### Deleting files
This should only be done if the files in question have been backed up or are
owned by a patient not qualified for a study. If this action is completed ALL
mechanical waveform files on the raspberry pi will be deleted. Go to `Full Clean` for this.

#### Gathering patient data
If you desire to collect all of a patient's mechanical waveform data and store it
in a patient unique location then click the `Enroll` button. First you will be
asked to enter the raspberry pi name, after doing this, all files on the pi will be backed
up. Then you will be asked to select all files belonging to a specific patient. Do this and
input a patient unique identifier. If the identifier is not
unique then waveform data from one patient may be confused with waveform data from
another. After inputting a unique identifier, all data will be moved to a patient
specific folder, and data on the pi will be deleted.

[1]: https://github.com/hahnicity/ucdpv_vent_infrastructure
[2]: https://ucdavis.app.box.com/s/b9wn4bux6piwhy3kzfs7lj6wpu55tiav
[3]: https://docs.ansible.com/ansible/playbooks_vault.html
