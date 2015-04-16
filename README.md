# Racktables Python API

This was forked from https://github.com/RackTables/racktables-contribs/tree/master/rtapi

I wanted to expand on the original rtapi and didn't like the coding standard for sql queries. 

So there is some left to rewrite and much left to add. 

## Original Author

Robert Vojcik (robert@vojcik.net)

## TODO

  * Tag support
  * Support for containers, like virtual clusters
  * Rewrite all calls to MySQLdb to use their own parameter expansion

# Example

The API frontend has changed some from the original. 

    import ipaddr
    import MySQLdb
    import rtapi

    # Create connection to database
    try:
        # Create connection to database
        db = MySQLdb.connect(host='hostname',port=3306, passwd='mypass',db='racktables',user='racktables)
    except MySQLdb.Error ,e:
        print "Error %d: %s" % (e.args[0],e.args[1])
        sys.exit(1)

    # Initialize rtapi with database connection
    rt = rtapi.RTObject(db)

    # List all objects from database
    for (object_id, object_name) in rt.Objects:
      print object_id, object_name

Example of use of generators in new API. 

    rt = rtapi.RTObject(db)

    # List all IPv4 Networks
    for network in rt.IPv4Networks():
      print network.name, network
