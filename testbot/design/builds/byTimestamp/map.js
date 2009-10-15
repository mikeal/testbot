function (doc) {
  if (doc.type == "build" && doc.timestamp) {
    emit(doc.timestamp, doc);
  }
}