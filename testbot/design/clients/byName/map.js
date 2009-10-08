function (doc) {
  if (doc.type == "client") {
    emit(doc.name, doc);
  }
}