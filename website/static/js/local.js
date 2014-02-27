$('#nav-search').on('click', function() {
  $(this).toggleClass('show hidden');
  $(this).removeClass('animated flipInX');
  $("#nav-search-close").toggleClass('show hidden');
  $("#nav-search-form").toggleClass('show hidden animated flipInX');
  return false;
});

$('#nav-search-close').on('click', function() {
  $(this).toggleClass('show hidden');
  $("#nav-search").toggleClass('show hidden animated flipInX');
  $("#nav-search-form").toggleClass('show hidden animated flipInX');
  return false;
});
