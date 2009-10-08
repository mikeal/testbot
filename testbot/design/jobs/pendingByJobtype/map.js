function (doc) {
  if (doc.type == 'job' && doc.status == 'pending') {
    emit([doc.jobtype, doc.creationdt], doc);
  }
}