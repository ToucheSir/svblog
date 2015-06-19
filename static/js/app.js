$(() => {
  const editor = new Quill('#post-text-editor', {
    theme: 'snow',
    modules: {
      toolbar: {
        container: '#post-text-toolbar'
      }
    }
  });
});
