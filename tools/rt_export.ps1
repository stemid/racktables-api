# This exports all VMs from vSphere with information relevant to a 
# Racktables import.
# by Stefan Midjich <swehack@gmail.com>
#
# For reference: https://pubs.vmware.com/vsphere-55/topic/com.vmware.powercli.cmdletref.doc/VirtualMachine.html

add-pssnapin VMware.VimAutomation.Core
Set-PowerCLIConfiguration -invalidCertificateAction 'ignore' -confirm:$false
Connect-VIServer -Server 10.220.100.220 -Protocol https

# This is the tag group with customer names in vSphere.
$customer_tag = 'Customer Names'
$vms = (get-vm)
$results = @()

foreach($vm in $vms) {
  $row = "" | select Folder, Name, HostName, NIC, IP, VLAN, OperatingSystem, CustomerTag, Tags, Host, Cluster
  $row.Folder = $vm.Folder
  $row.Name = $vm.Name
  $row.HostName = $vm.Guest.HostName
  $row.OperatingSystem = $vm.Guest.OSFullName
  $row.NIC = ($vm.Guest.Nics | foreach-object {$_.Device}) -join ','
  $row.IP = ($vm.Guest | ForEach-Object {$_.IPAddress} | where-object {
      $_.split('.').length -eq 4
  }) -join ','
  $row.VLAN = ($vm | get-networkadapter | foreach-object {
      $_.NetworkName
  }) -join ','
  # Tags requires PowerCLI 5.5 and vSphere 5.1.
  $row.Tags = ($vm | get-tagassignment | foreach-object {
      $_.Tag.Name
  }) -join ','
  $row.CustomerTag = ($vm | get-tagassignment | foreach-object {
      $_.Tag
  } | where-object {$_.Category -eq $customer_tag}).Name
  $row.Host = $vm.VMHost.Name
  $row.Cluster = (get-cluster -vm $vm)
  $results += $row
}

$results | export-csv -path "C:\vSphere scripts\VM CSV export\racktables.csv" -UseCulture -NoTypeInformation
