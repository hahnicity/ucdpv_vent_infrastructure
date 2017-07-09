# ucdpv_vent_infrastructure
The [UCDPV vent infrastructure][1] is designed to allow anyone to use off the shelf
commercial products to set up a fully functional clinical informatics study
for collecting of mechanical ventilator data.

In this README installation and usage instructions are provided.

## Hardware Prerequisites
The following components will be necessary before attempting to install the UCDPV
vent infrastructure:

 1. A Raspberry Pi device and power cable.
 2. A shielded DB-9 to USB serial cable
 3. An RS-232 optical isolator
 4. A linux/OSX computer. If windows is desired, then it must have Cygwin.

## PB-840 Ventilator Setup
The PB-840 ventilator will need to undergo several steps to enable data output
from the RS-232 serial port.

Consult your PB-840 technical manual for additional details about ventilator setup.

XXX need jason to get back to me on this
XXX which serial port are we using? 1, 2, or 3. Probably #1

## Software Installion dependencies
Once hardware dependencies are satisfied, and the ventilator is set up, the
user will need to begin installing software on their local machine to set up the
RPi devices. First, the user needs to install virtualenv. Using pip this can be
done via

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

##### Final Details
The setup given is sufficient to begin collection of ventilator data, but
will not ensure correct operation with the clinicalsupervisor. If you desire compatibility with the clinicalsupervisor then see the details on setting up the clinicalsupervisor
and then finalize your installation of the Raspberry Pi's via ansible.

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

#### Raspberry Pi Initial setup
Since Ansible was installed in previous steps and the provisioning LAN is now setup,
plug an ethernet cable from the router into the raspberry pi. Navigate
to the `raspi/ansible` directory

    cd raspi/ansible

and modify the file at `group_vars/rpis`.
Here enter the production network's wireless SSID and password.
Also enter the network's ntp server host ip addresses. Finally
installation can proceed. To install all necessary software

    ansible-playbook -u pi --ask-sudo -i inventory/rpi_initial rpi_pre_hostname_install.yml

When prompted for the password enter "raspberry" per standard setup. Now your
system will be minimally set up to extract ventilator data. However, they will
not be able to interact with the clinicalsupervisor yet. Next steps involve setting
up the clinicalsupervisor, and networking your Raspberry Pi's so that they
receive DNS addresses.

#### Raspberry Pi Final Setup
Now that the clinicalsupervisor is set up, the Raspberry Pi's have DNS addresses,
and configuration details for the `retriever` user are finished, you can complete
the setup of the Raspberry Pi's. This will change all hostnames on the Raspberry Pi's
in accordance with your DNS profile, and will set up SSH links between the clinicalsupervisor
and the Raspberry Pi's

    ansible-playbook -u pi --ask-sudo -i inventory/<inventory file> rpi_install.yml

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

### Restricting SSH Commands
Clinicalsupervisor should only communicate with the Raspberry Pi's via a limited
set of commands. As a result 3 new users are set up on the clinicalsupervisor and
the Raspberry Pi's: `backup`, `cleaner`, and `lister`.

`backup` is meant only to backup all data in the `/home/pi/Data` directory. `cleaner`
is meant to perform deletions of files when necessary, and `lister` is designed to
only list the files in the data directory.

As the sysadmin, you will need to create a passwordless, public/private keypair for
the `retriever` user on the clinicalsupervisor host. Then, take the public key for
this key pair and paste it into `group_vars/rpis` for the `retriever_pub_key` variable.
After pasting the public key it should look like this:

    retriever_pub_key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQChlZwB1+fMhvqVfP2ZV1pH8kH9rwpTYsBbcvCeLZ/cfeScn91RI3M9eWhdTOWD1O4T5FhgWkCjaVbDqDjKFmknSGXa9NaIicMX8fSUZ7Kda0PvfJBwwtewgS8uzhuxgXG2ltflh11W6c0c1sNI2XaGEZ7LlAE3bbkzP1PWvWCtqC8+s4ZeSNDFE2K0GCJmckbb0xw4CNFoVHj10kCdD1z/vGCV1YKKmUn7WRYL2Rcpw7HIOlprzHPhSgg2rda8GvqN0N8C9pbY+XMLiG0bU+iD8dgtg0h5gBBKNmicHp+SQQdtjlZcBtLYDDhTRI5tAKvpHSFqc8PK+n1WAaMWeY3x retriever@foo

After performing this action you will need to re-update your Raspberry Pi devices
with this public key.

### OSX

    ansible-playbook -i inventory/<inv file name> clinicalsupervisor_install_osx.yml

### Debian

    ansible-playbook -i inventory/<inv file name> clinicalsupervisor_install_debian.yml

## Usage

### Raspberry Pi
To use the raspberry pis, first get a micro-usb power cable and usb-to-RS232 serial
cable. Take the raspberry pi with these components to the ventilator and hook the DB-9 cable to the
the primary serial port of the PB-840 ventilator and the usb side to the raspberry pi. Power
the raspberry pi with the power cable, and ensure the ventilator is currently
operating. Once the ventilator is operating waveform data collection will begin.

XXX Which serial port? Probably #1 but be sure.

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

## Security
Given you are working in a hospital environment, security will be a concern about
any system used. As a result, we have taken steps to harden this system against intrusion.
While no security protocol is perfect, the steps outlined, if followed, will ensure
your system poses the minimal amount of security risk to the broader hospital infrastructure, and ensure the system will be able to survive if one component is compromised.

### Raspberry Pi Hardening

#### User Passwords
It is **highly advised** to change the default user password for the Raspberry Pi's.
First, generate a password and hash it, via the steps outlined [here][4]. Then go
to `group_vars/rpis` and modify the `pi_user_password` variable. Since you should
not risk exposing a hash publically, encrypt the `group_vars/rpis` file using
[ansible-vault][3].

    ansible-vault encrypt group_vars/rpis

#### Pi Storage
The Raspberry Pi's are generally not vulnerable while they are attached to a patient
in the ICU given the amount of monitoring a patient receives there, but may be
vulnerable to exploit in an intermediary storage location if located in a common storage area
of the hospital. Together with hospital engineering, network, and security teams you **must**
make a **conscious determination** on what is the best storage procedure for the Pi's.

#### Pi Networking
Raspberry Pi's should not be networked to communicate with anything via outbound
connection. It is advised to perform firewalling at the network level to not allow
outbound communications from the RPi's.

#### PHI capability
Currently, this system does not have the ability to be used for PHI data. This
would require the modification of the system to either perform

 * resting encryption of all data
 * immediate transfer of PHI data to a more secure location

If this capability is desired we would be happy to assist in the update of this
platform.

### Clinicalsupervisor Hardening
#### Basics
The primary goal here is to ensure that an infection of one of the Raspberry Pi devices
does not compromise the clinicalsupervisor where data resides.

 1. Ensure the clinicalsupervisor resides on a health-system monitored server in a datacenter. This ensures only privileged users will have access to the computing device, and links the health of your server to the IT capabilities of your institution
 2. Ensure that the clinicalsupervisor can only accept incoming communications fromapproved IP addresses. Do not allow the RPi's to communicate with the clinicalsupervisor, there is no reason why they should anyways. This whitelisting of IP's can either take place on the host, or the network level.

#### Others
Security is a deep field, and it is difficult to enumerate all the things necessary
to properly secure a server. We have chosen to remove some security details for the
clinicalsupervisor like SSH configuration because we believe these things are better
left in the hands of the user. If there are any other security details you feel
that we've missed pull requests are always welcome :)


[1]: https://github.com/hahnicity/ucdpv_vent_infrastructure
[2]: https://ucdavis.app.box.com/s/b9wn4bux6piwhy3kzfs7lj6wpu55tiav
[3]: https://docs.ansible.com/ansible/playbooks_vault.html
[4]: https://docs.ansible.com/ansible/faq.html#how-do-i-generate-crypted-passwords-for-the-user-module
