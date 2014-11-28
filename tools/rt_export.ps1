# This exports all VMs from vSphere with information relevant to a Racktables import.
# by Stefan Midjich <swehack@gmail.com>
#
# For reference: https://pubs.vmware.com/vsphere-55/topic/com.vmware.powercli.cmdletref.doc/VirtualMachine.html

add-pssnapin VMware.VimAutomation.Core
Set-PowerCLIConfiguration -invalidCertificateAction 'ignore' -confirm:$false
Connect-VIServer -Server 10.220.100.220 -Protocol https

$vms = (get-vm)
$results = @()

foreach($vm in $vms) {
  $row = "" | select Folder, Name, HostName, NIC, IP, VLAN, OperatingSystem, Host, Cluster
  $row.Folder = $vm.Folder
  $row.Name = $vm.Name
  $row.HostName = $vm.Guest.HostName
  $row.OperatingSystem = $vm.Guest.OSFullName
  $row.NIC = ($vm.Guest.Nics | foreach-object {$_.Device}) -join ','
  $row.IP = ($vm.Guest | ForEach-Object {$_.IPAddress} | where-object {$_.split('.').length -eq 4}) -join ','
  $row.VLAN = ($vm | get-networkadapter | foreach-object {$_.NetworkName}) -join ','
  $row.Host = $vm.VMHost.Name
  $row.Cluster = (get-cluster -vm $vm)
  $results += $row
}

$results | export-csv -path "C:\vSphere scripts\VM CSV export\racktables.csv" -UseCulture -NoTypeInformation
