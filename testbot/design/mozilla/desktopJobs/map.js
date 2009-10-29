function (doc) {
  if (doc.type == 'job' && job.status == 'pending') {
    if (doc.jobtype == 'mochitest' || doc.jobtype == 'reftest' || doc.jobtype 'mochitest-chrome') {
      if (doc.platform['os.sysname'] == 'Linux') {
        emit([doc.platform["os.sysname"], doc.jobtype, doc.creationdt], doc);
      } 
    }
  }
}