function (doc) {
  if (doc.type == 'job' && doc.build) {
    emit(doc.build._id, doc);
  }
}